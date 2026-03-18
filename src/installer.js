'use strict';

const fs = require('fs');
const path = require('path');
const { INSTALL_TARGETS, userHome } = require('./constants');

function buildInstallPlan(options = {}, targetKeys = [], scope, mode = 'symlink') {
  if (options.dest) {
    return {
      mode: 'copy',
      scope: 'dest',
      targets: [
        {
          key: 'dest',
          baseDir: absPath(options.dest),
        },
      ],
    };
  }

  const selectedTargets = targetKeys.length
    ? INSTALL_TARGETS.filter((target) => targetKeys.includes(target.key))
    : INSTALL_TARGETS;

  const resolvedScope =
    scope || (options.global ? 'global' : options.projectPath !== undefined ? 'project' : 'global');
  const baseDir =
    resolvedScope === 'global' ? userHome() : absPath(options.projectPath || process.cwd());

  return {
    mode,
    scope: resolvedScope,
    baseDir,
    targets: selectedTargets.map((target) => ({
      key: target.key,
      baseDir: path.join(baseDir, target.folder, 'skills'),
    })),
  };
}

function hasExistingSkills(plan, skills) {
  for (const skill of skills) {
    for (const target of plan.targets) {
      if (fs.existsSync(path.join(target.baseDir, skill.name))) {
        return true;
      }
    }
  }
  return false;
}

async function installSkills(skills, plan, force) {
  const results = [];

  for (const skill of skills) {
    const sourceDir = path.resolve(skill.path);
    const useSymlink = plan.mode === 'symlink' && !skill.external;

    for (const target of plan.targets) {
      const targetDir = path.join(target.baseDir, skill.name);

      if (fs.existsSync(targetDir)) {
        if (force) {
          await fs.promises.rm(targetDir, { recursive: true, force: true });
        } else {
          results.push({
            skill: skill.name,
            path: targetDir,
            skipped: true,
            mode: plan.mode,
          });
          continue;
        }
      }

      if (!useSymlink) {
        await copyDir(skill.path, targetDir);
        results.push({
          skill: skill.name,
          path: targetDir,
          skipped: false,
          mode: 'copy',
        });
        continue;
      }

      const symlinkCreated = await createSymlink(sourceDir, targetDir);
      if (!symlinkCreated) {
        await copyDir(skill.path, targetDir);
        results.push({
          skill: skill.name,
          path: targetDir,
          skipped: false,
          mode: 'copy',
          symlinkFailed: true,
          sourcePath: sourceDir,
        });
        continue;
      }

      results.push({
        skill: skill.name,
        path: targetDir,
        skipped: false,
        mode: 'symlink',
        sourcePath: sourceDir,
      });
    }
  }

  return results;
}

async function createSymlink(target, linkPath) {
  try {
    const linkDir = path.dirname(linkPath);
    await fs.promises.mkdir(linkDir, { recursive: true });

    if (fs.existsSync(linkPath)) {
      await fs.promises.rm(linkPath, { recursive: true, force: true });
    }

    const linkTarget =
      process.platform === 'win32' ? path.resolve(target) : path.relative(linkDir, target);
    const linkType = process.platform === 'win32' ? 'junction' : 'dir';
    await fs.promises.symlink(linkTarget, linkPath, linkType);
    return true;
  } catch {
    return false;
  }
}

async function copyDir(source, destination) {
  if (fs.existsSync(destination)) {
    await fs.promises.rm(destination, { recursive: true, force: true });
  }
  await fs.promises.mkdir(destination, { recursive: true });
  const entries = await fs.promises.readdir(source, { withFileTypes: true });
  for (const entry of entries) {
    const sourcePath = path.join(source, entry.name);
    const destinationPath = path.join(destination, entry.name);
    if (entry.isDirectory()) {
      await copyDir(sourcePath, destinationPath);
    } else {
      await fs.promises.copyFile(sourcePath, destinationPath);
    }
  }
}

function absPath(value) {
  if (!value) {
    throw new Error('Path is empty.');
  }
  return path.isAbsolute(value) ? value : path.resolve(process.cwd(), value);
}

module.exports = {
  absPath,
  buildInstallPlan,
  createSymlink,
  copyDir,
  hasExistingSkills,
  installSkills,
};
