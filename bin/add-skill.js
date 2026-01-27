#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');
const { spawnSync } = require('child_process');
const defaultRepoURL = 'https://github.com/geocine/geocine-skills.git';
let promptsModule = null;

function usage() {
  console.log('@geocine/add-skill');
  console.log('');
  console.log('Commands:');
  console.log('  install   Interactive install (default)');
  console.log('  list      List available skills');
  console.log('  help      Show this help');
  console.log('');
  console.log('Install options:');
  console.log('  --dest <path>        Install into a single destination');
  console.log('  --global             Install to user-level locations');
  console.log('  --project [path]     Install to project-level locations (default: current directory)');
  console.log('  --skills <list>      Comma list of skill names to install');
  console.log('  --all                Install all skills');
  console.log('  --force              Overwrite existing skills');
  console.log('  --no-pull            Skip git pull when repo already exists');
  console.log('  --yes                Skip prompts (defaults to all skills + global)');
}

async function main() {
  const { command, options } = parseArgs(process.argv.slice(2));
  if (!command || command === 'install') {
    await runInstall(options);
    return;
  }
  if (command === 'list') {
    await runList(options);
    return;
  }
  if (command === 'help') {
    usage();
    return;
  }
  console.error(`Unknown command: ${command}`);
  usage();
  process.exit(1);
}

async function runList(options) {
  const repoRoot = await resolveRepoRoot(options);
  const skills = findSkills(repoRoot);
  console.log('Available skills:');
  for (const skill of skills) {
    console.log(` - ${skill.name}`);
  }
}

async function runInstall(options) {
  const repoRoot = await resolveRepoRoot(options);
  const skills = findSkills(repoRoot);

  const selectedSkills = await selectSkills(skills, options);
  const destinations = await resolveDestinations(options);

  let force = options.force;
  if (!force && !options.yes && hasExistingSkills(destinations, selectedSkills)) {
    const overwrite = await promptYesNo('Overwrite existing skills?', false);
    if (overwrite) {
      force = true;
    }
  }

  await installSkills(selectedSkills, destinations, force);
  console.log('Done. Restart your editor to pick up new skills.');
}

async function resolveRepoRoot(options) {
  const cwd = process.cwd();
  const found = findRepoRootUp(cwd);
  if (found) {
    return found;
  }

  const scriptRoot = findRepoRootUp(path.resolve(__dirname, '..'));
  if (scriptRoot) {
    return scriptRoot;
  }

  const defaultPath = path.join(userHome(), '.geocine-skills');
  if (pathExists(defaultPath)) {
    if (!options.noPull && pathExists(path.join(defaultPath, '.git'))) {
      if (options.yes || await promptYesNo(`Update repo at ${defaultPath} with git pull?`, true)) {
        runGit(defaultPath, ['pull']);
      }
    }
    return defaultPath;
  }

  if (options.yes || await promptYesNo(`Clone repo to ${defaultPath}?`, true)) {
    runGit('', ['clone', defaultRepoURL, defaultPath]);
    return defaultPath;
  }

  throw new Error('No repo found. Run via npx or clone the repo first.');
}

function findRepoRootUp(start) {
  let dir = start;
  while (true) {
    if (dirHasSkills(dir)) {
      return dir;
    }
    const parent = path.dirname(dir);
    if (parent === dir) {
      return null;
    }
    dir = parent;
  }
}

function dirHasSkills(root) {
  const skillsRoot = path.join(root, 'skills');
  if (dirHasSkillEntries(skillsRoot)) {
    return true;
  }
  return dirHasSkillEntries(root);
}

function dirHasSkillEntries(base) {
  if (!dirExists(base)) {
    return false;
  }
  const entries = fs.readdirSync(base, { withFileTypes: true });
  return entries.some((entry) => entry.isDirectory() && pathExists(path.join(base, entry.name, 'SKILL.md')));
}

function findSkills(repoRoot) {
  const skillsRoot = path.join(repoRoot, 'skills');
  const base = dirExists(skillsRoot) ? skillsRoot : repoRoot;

  const entries = fs.readdirSync(base, { withFileTypes: true });
  const skills = entries
    .filter((entry) => entry.isDirectory() && pathExists(path.join(base, entry.name, 'SKILL.md')))
    .map((entry) => ({
      name: entry.name,
      path: path.join(base, entry.name),
    }))
    .sort((a, b) => a.name.localeCompare(b.name));

  if (!skills.length) {
    throw new Error('No skills found in repo.');
  }

  return skills;
}

async function selectSkills(skills, options) {
  if (options.all) {
    return skills;
  }

  if (options.skills && options.skills.length) {
    return filterSkillsByName(skills, options.skills);
  }

  if (options.yes) {
    return skills;
  }

  // Ask if user wants all skills or custom selection
  const prompts = loadPrompts();
  const modeResponse = await prompts({
    type: 'select',
    name: 'mode',
    message: 'Which skills to install?',
    choices: [
      { title: 'All skills', value: 'all' },
      { title: 'Choose specific skills', value: 'custom' },
    ],
  }, { onCancel });

  if (modeResponse.mode === 'all') {
    return skills;
  }

  // Custom selection
  const response = await prompts({
    type: 'multiselect',
    name: 'selected',
    message: 'Select skills',
    choices: skills.map((skill) => ({
      title: skill.name,
      value: skill.name,
    })),
  }, { onCancel });

  if (!response.selected || response.selected.length === 0) {
    throw new Error('No skills selected.');
  }
  return filterSkillsByName(skills, response.selected);
}

function filterSkillsByName(skills, names) {
  const nameSet = new Set(names.map((name) => name.toLowerCase()));
  const selected = skills.filter((skill) => nameSet.has(skill.name.toLowerCase()));
  if (!selected.length) {
    throw new Error('No matching skills selected.');
  }
  return selected;
}

async function resolveDestinations(options) {
  if (options.dest) {
    return [absPath(options.dest)];
  }

  const home = userHome();

  // If --global flag is set, install to user locations
  if (options.global) {
    return getGlobalPaths(home);
  }

  // If --project flag is set, install to project locations
  if (options.projectPath !== undefined) {
    const projectRoot = options.projectPath || process.cwd();
    return getProjectPaths(absPath(projectRoot));
  }

  // --yes defaults to global
  if (options.yes) {
    return getGlobalPaths(home);
  }

  // Interactive: ask user
  const prompts = loadPrompts();
  const response = await prompts({
    type: 'select',
    name: 'location',
    message: 'Install to project or global (user)?',
    choices: [
      { title: 'Global (user-level)', value: 'global' },
      { title: 'Project', value: 'project' },
    ],
  }, { onCancel });

  if (response.location === 'project') {
    const projectPrompt = await prompts({
      type: 'text',
      name: 'root',
      message: 'Project path',
      initial: process.cwd(),
    }, { onCancel });
    const projectRoot = projectPrompt.root || process.cwd();
    return getProjectPaths(absPath(projectRoot));
  }

  return getGlobalPaths(home);
}

function getGlobalPaths(home) {
  const codexHome = process.env.CODEX_HOME && process.env.CODEX_HOME.trim()
    ? process.env.CODEX_HOME.trim()
    : path.join(home, '.codex');

  return [
    path.join(codexHome, 'skills'),
    path.join(home, '.cursor', 'skills'),
    path.join(home, '.copilot', 'skills'),
    path.join(home, '.claude', 'skills'),
    path.join(home, '.config', 'opencode', 'skills'),
  ];
}

function getProjectPaths(projectRoot) {
  return [
    path.join(projectRoot, '.codex', 'skills'),
    path.join(projectRoot, '.cursor', 'skills'),
    path.join(projectRoot, '.github', 'skills'),
    path.join(projectRoot, '.claude', 'skills'),
    path.join(projectRoot, '.opencode', 'skills'),
  ];
}

function hasExistingSkills(destinations, skills) {
  for (const dest of destinations) {
    for (const skill of skills) {
      if (pathExists(path.join(dest, skill.name))) {
        return true;
      }
    }
  }
  return false;
}

async function installSkills(skills, destinations, force) {
  for (const dest of destinations) {
    await fs.promises.mkdir(dest, { recursive: true });
    for (const skill of skills) {
      const target = path.join(dest, skill.name);
      if (pathExists(target)) {
        if (force) {
          await fs.promises.rm(target, { recursive: true, force: true });
        } else {
          console.log(`Skip ${skill.name} -> ${target} (already exists)`);
          continue;
        }
      }
      await copyDir(skill.path, target);
      console.log(`Installed ${skill.name} -> ${target}`);
    }
  }
}

async function copyDir(src, dst) {
  await fs.promises.mkdir(dst, { recursive: true });
  const entries = await fs.promises.readdir(src, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const dstPath = path.join(dst, entry.name);
    if (entry.isDirectory()) {
      await copyDir(srcPath, dstPath);
    } else {
      await fs.promises.copyFile(srcPath, dstPath);
    }
  }
}

function parseArgs(argv) {
  let command = '';
  const options = {
    dest: '',
    global: false,
    projectPath: undefined,
    skills: [],
    all: false,
    force: false,
    noPull: false,
    yes: false,
  };

  const args = [...argv];
  if (args[0] && !args[0].startsWith('-')) {
    command = args.shift();
  }

  while (args.length) {
    const arg = args.shift();
    switch (arg) {
      case '--dest':
        options.dest = args.shift() || '';
        break;
      case '--global':
        options.global = true;
        break;
      case '--project': {
        const next = args[0];
        // Check if next arg is a path (not another flag)
        if (next && !next.startsWith('-')) {
          options.projectPath = args.shift();
        } else {
          options.projectPath = '';
        }
        break;
      }
      case '--skills':
        options.skills = splitList(args.shift() || '');
        break;
      case '--all':
        options.all = true;
        break;
      case '--force':
        options.force = true;
        break;
      case '--no-pull':
        options.noPull = true;
        break;
      case '--yes':
      case '-y':
        options.yes = true;
        break;
      case '--help':
      case '-h':
        command = 'help';
        break;
      default:
        if (arg.startsWith('--skills=')) {
          options.skills = splitList(arg.split('=')[1] || '');
          break;
        }
        if (arg.startsWith('--project=')) {
          options.projectPath = arg.split('=')[1] || '';
          break;
        }
        break;
    }
  }

  return { command, options };
}

function splitList(value) {
  return String(value)
    .replace(/[; ]/g, ',')
    .split(',')
    .map((entry) => entry.trim())
    .filter(Boolean);
}

function promptText(message, initial) {
  const prompts = loadPrompts();
  return prompts({
    type: 'text',
    name: 'value',
    message,
    initial,
  }, { onCancel }).then((res) => res.value || '');
}

function promptYesNo(message, initial) {
  const prompts = loadPrompts();
  return prompts({
    type: 'confirm',
    name: 'value',
    message,
    initial,
  }, { onCancel }).then((res) => Boolean(res.value));
}

function runGit(cwd, args) {
  const result = spawnSync('git', args, { stdio: 'inherit', cwd: cwd || undefined });
  if (result.error) {
    throw result.error;
  }
  if (result.status !== 0) {
    throw new Error('git command failed');
  }
}

function userHome() {
  return process.env.USERPROFILE || os.homedir();
}

function absPath(value) {
  if (!value) {
    throw new Error('Path is empty.');
  }
  return path.isAbsolute(value) ? value : path.resolve(process.cwd(), value);
}

function pathExists(p) {
  try {
    fs.accessSync(p);
    return true;
  } catch (err) {
    return false;
  }
}

function dirExists(p) {
  try {
    return fs.statSync(p).isDirectory();
  } catch (err) {
    return false;
  }
}

function onCancel() {
  console.log('Cancelled.');
  process.exit(1);
}

function loadPrompts() {
  if (!promptsModule) {
    try {
      promptsModule = require('prompts');
    } catch (err) {
      throw new Error('Missing dependency "prompts". Run `npm install` or use the npx command.');
    }
  }
  return promptsModule;
}

main().catch((err) => {
  console.error('Error:', err.message);
  process.exit(1);
});
