'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const { runGit } = require('./git');

const EXTERNAL_SKILLS = [
  {
    name: 'planpack',
    description:
      'Bootstrap and operate a planpack — a portable, git-versioned planning pack (graph wiki + comments) shared between humans and LLM agents, dropped into any repository as a planpack/ folder. Use when the user says planpack, planning pack, plan graph, wants a shared planning/brainstorming space with an LLM, asks to set up planpack in a repo, or asks to resolve plan comments / open questions in a planpack.',
    shortDescription: 'Bootstrap a shared planning pack (graph wiki + comments)',
    repository: 'any',
    author: 'geocine',
    external: {
      repoUrl: 'https://github.com/geocine/planpack.git',
      ref: 'main',
      // SKILL.md lives at the repo root; template/ must ship with the skill.
      path: '.',
    },
  },
];

function cloneExternalSkill(skill) {
  return {
    ...skill,
    external: skill.external ? { ...skill.external } : undefined,
    path: skill.path || '',
  };
}

function getExternalSkills() {
  return EXTERNAL_SKILLS.map(cloneExternalSkill);
}

function getExplicitExternalSkills(names = []) {
  const requested = new Set((names || []).map((name) => String(name).toLowerCase()));
  return EXTERNAL_SKILLS.filter((skill) => requested.has(skill.name.toLowerCase())).map(cloneExternalSkill);
}

function isExplicitExternalSkillName(name) {
  const normalized = String(name || '').toLowerCase();
  return EXTERNAL_SKILLS.some((skill) => skill.name.toLowerCase() === normalized);
}

async function materializeSkillSources(skills, deps = {}) {
  const externalSkills = skills.filter((skill) => skill && skill.external);
  if (!externalSkills.length) {
    return {
      skills,
      cleanup: async () => {},
    };
  }

  const tempBaseDir =
    deps.tempBaseDir ||
    fs.mkdtempSync(path.join(deps.tempParentDir || os.tmpdir(), 'geocine-skills-external-'));
  const groupedSkills = groupByRepo(externalSkills);
  const preparedByName = new Map();

  try {
    for (let index = 0; index < groupedSkills.length; index += 1) {
      const group = groupedSkills[index];
      const checkoutDir = path.join(tempBaseDir, `repo-${index}`);
      checkoutRepoGroup(group, checkoutDir, deps);

      for (const skill of group.skills) {
        const skillPath = resolveExternalSkillPath(checkoutDir, skill.external.path);
        if (!fs.existsSync(path.join(skillPath, 'SKILL.md'))) {
          throw new Error(
            `External skill "${skill.name}" was not found at ${skill.external.repoUrl || skill.external.path}.`
          );
        }

        preparedByName.set(skill.name.toLowerCase(), {
          ...skill,
          path: skillPath,
        });
      }
    }

    return {
      skills: skills.map((skill) => preparedByName.get(skill.name.toLowerCase()) || skill),
      cleanup: async () => {
        fs.rmSync(tempBaseDir, { recursive: true, force: true });
      },
    };
  } catch (error) {
    fs.rmSync(tempBaseDir, { recursive: true, force: true });
    throw error;
  }
}

function groupByRepo(skills) {
  const groups = new Map();

  for (const skill of skills) {
    const key = `${skill.external.repoUrl}#${skill.external.ref || 'main'}`;
    if (!groups.has(key)) {
      groups.set(key, {
        repoUrl: skill.external.repoUrl,
        ref: skill.external.ref || 'main',
        paths: new Set(),
        skills: [],
      });
    }

    const group = groups.get(key);
    group.paths.add(skill.external.path);
    group.skills.push(skill);
  }

  return Array.from(groups.values());
}

function checkoutRepoGroup(group, checkoutDir, deps = {}) {
  const runGitCommand = deps.runGitCommand || runGit;
  const repoUrl = group.repoUrl;
  const ref = group.ref || 'main';
  const sparsePaths = Array.from(group.paths).filter((entry) => !isWholeRepoPath(entry));
  const cloneWholeRepo = !sparsePaths.length || Array.from(group.paths).some(isWholeRepoPath);

  fs.rmSync(checkoutDir, { recursive: true, force: true });
  fs.mkdirSync(path.dirname(checkoutDir), { recursive: true });

  if (!cloneWholeRepo) {
    try {
      runGitCommand(
        ['clone', '--depth', '1', '--filter=blob:none', '--sparse', '--branch', ref, repoUrl, checkoutDir],
        { repoUrl }
      );
      runGitCommand(['sparse-checkout', 'set', '--cone', ...sparsePaths], {
        cwd: checkoutDir,
        repoUrl,
      });
      return;
    } catch {
      fs.rmSync(checkoutDir, { recursive: true, force: true });
    }
  }

  runGitCommand(['clone', '--depth', '1', '--branch', ref, repoUrl, checkoutDir], { repoUrl });
}

function isWholeRepoPath(skillPath) {
  const normalized = String(skillPath || '')
    .replace(/\\/g, '/')
    .trim();
  return !normalized || normalized === '.' || normalized === '/';
}

function resolveExternalSkillPath(checkoutDir, skillPath) {
  if (isWholeRepoPath(skillPath)) {
    return checkoutDir;
  }

  return path.join(checkoutDir, ...String(skillPath).split(/[\\/]+/).filter(Boolean));
}

module.exports = {
  EXTERNAL_SKILLS,
  getExternalSkills,
  getExplicitExternalSkills,
  isExplicitExternalSkillName,
  materializeSkillSources,
};
