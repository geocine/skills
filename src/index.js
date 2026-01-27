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
  console.log('  --filter <text>      Filter skills by name, description, or repository');
  console.log('  --details            Show full descriptions in interactive selection');
  console.log('');
  console.log('List options:');
  console.log('  --filter <text>      Filter skills by name, description, or repository');
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
  let skills = findSkills(repoRoot);
  skills = applyListFilter(skills, options);
  console.log('Available skills:');
  for (const skill of skills) {
    const short = skill.shortDescription || '';
    const repository = skill.repository || 'any';
    const suffix = short ? ` - ${short}` : '';
    console.log(` - ${skill.name}${suffix} [${repository}]`);
  }
}

async function runInstall(options) {
  const repoRoot = await resolveRepoRoot(options);
  const skills = findSkills(repoRoot);

  // Use interactive Ink UI if no automation flags are set
  const isInteractive = !options.yes && !options.all && !options.skills.length && !options.dest;
  
  if (isInteractive) {
    await runInkInstall(skills, options);
    return;
  }

  // Non-interactive mode
  const selectedSkills = await selectSkillsNonInteractive(skills, options);
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

async function runInkInstall(skills, options) {
  const React = require('react');
  const { render } = require('ink');
  const App = require('./cli/App');

  const handleInstall = async (selectedSkills, selectedEditors, destination, force) => {
    const home = userHome();
    const baseDir = destination === 'global' ? home : process.cwd();
    const isGlobal = destination === 'global';
    
    // Build paths only for selected editors (use localFolder for project installs)
    const destinations = selectedEditors.map((editor) => {
      const folder = isGlobal ? editor.folder : (editor.localFolder || editor.folder);
      return path.join(baseDir, folder, 'skills');
    });
    
    const results = [];
    for (const dest of destinations) {
      await fs.promises.mkdir(dest, { recursive: true });
      for (const skill of selectedSkills) {
        const target = path.join(dest, skill.name);
        if (pathExists(target)) {
          if (force) {
            await fs.promises.rm(target, { recursive: true, force: true });
          } else {
            results.push({ skill: skill.name, path: target, skipped: true });
            continue;
          }
        }
        await copyDir(skill.path, target);
        results.push({ skill: skill.name, path: target, skipped: false });
      }
    }
    return results;
  };

  // Clear screen before showing UI
  process.stdout.write('\x1b[2J\x1b[H');

  return new Promise((resolve) => {
    const { unmount, waitUntilExit } = render(
      React.createElement(App, { 
        skills, 
        onInstall: handleInstall,
        options 
      })
    );
    waitUntilExit().then(resolve);
  });
}

async function selectSkillsNonInteractive(skills, options) {
  const filteredSkills = applyListFilter(skills, options);
  if (options.filter && !filteredSkills.length) {
    throw new Error('No skills match the filter.');
  }

  if (options.all || options.yes) {
    return filteredSkills;
  }

  if (options.skills && options.skills.length) {
    return filterSkillsByName(filteredSkills, options.skills);
  }

  return filteredSkills;
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
      // Fetch + hard reset to avoid merge conflicts
      await runGitWithProgress(defaultPath, ['fetch', '--progress', 'origin'], 'Fetching latest skills');
      await runGitWithProgress(defaultPath, ['reset', '--hard', 'origin/main'], 'Updating skills repository');
    }
    return defaultPath;
  }

  await runGitWithProgress('', ['clone', '--progress', defaultRepoURL, defaultPath], 'Cloning skills repository');
  return defaultPath;
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
  const fromJson = loadSkillsJson(repoRoot);
  if (fromJson.length) {
    return fromJson;
  }

  const skillsRoot = path.join(repoRoot, 'skills');
  const base = dirExists(skillsRoot) ? skillsRoot : repoRoot;

  const entries = fs.readdirSync(base, { withFileTypes: true });
  const skills = entries
    .filter((entry) => entry.isDirectory() && pathExists(path.join(base, entry.name, 'SKILL.md')))
    .map((entry) => {
      const skillPath = path.join(base, entry.name);
      const skillFile = path.join(skillPath, 'SKILL.md');
      const { description } = readFrontmatter(skillFile);
      return {
        name: entry.name,
        path: skillPath,
        description,
        shortDescription: buildShortDescription(description),
        repository: 'any'
      };
    })
    .sort((a, b) => a.name.localeCompare(b.name));

  if (!skills.length) {
    throw new Error('No skills found in repo.');
  }

  return skills;
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
    filter: '',
    details: false,
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
      case '--filter':
      case '--search':
        options.filter = args.shift() || '';
        break;
      case '--details':
      case '--full':
        options.details = true;
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
        if (arg.startsWith('--filter=')) {
          options.filter = arg.split('=')[1] || '';
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

function applyListFilter(skills, options) {
  const query = (options.filter || '').trim().toLowerCase();
  if (!query) {
    return skills;
  }

  return skills.filter((skill) => {
    return [
      skill.name,
      skill.description,
      skill.shortDescription,
      skill.repository
    ]
      .filter(Boolean)
      .some((field) => field.toLowerCase().includes(query));
  });
}

function formatChoiceDescription(skill, options) {
  const repository = skill.repository || 'any';
  const base = options.details
    ? (skill.description || '')
    : (skill.shortDescription || '');

  if (!base) {
    return `Repo: ${repository}`;
  }

  return `${base} (Repo: ${repository})`;
}

function loadSkillsJson(repoRoot) {
  const skillsFile = path.join(repoRoot, 'skills.json');
  if (!pathExists(skillsFile)) {
    return [];
  }
  try {
    const raw = fs.readFileSync(skillsFile, 'utf8');
    const data = JSON.parse(raw);
    if (!Array.isArray(data)) {
      return [];
    }
    return data
      .filter((skill) => skill && typeof skill.name === 'string')
      .map((skill) => ({
        name: skill.name,
        description: skill.description || '',
        shortDescription: skill.shortDescription || buildShortDescription(skill.description),
        repository: skill.repository || 'any',
        path: skill.path ? path.join(repoRoot, skill.path) : ''
      }))
      .sort((a, b) => a.name.localeCompare(b.name));
  } catch (error) {
    return [];
  }
}

function buildShortDescription(description) {
  if (!description) {
    return '';
  }
  let base = String(description).replace(/\s+/g, ' ').trim();
  const cutTokens = [' Use when ', ' Use after ', ' Use for ', ' Use if ', ' Use to '];
  for (const token of cutTokens) {
    const idx = base.indexOf(token);
    if (idx > 0) {
      base = base.slice(0, idx).trim();
      break;
    }
  }

  base = base.replace(/\s*\([^)]*\)\s*/g, ' ').replace(/\s+/g, ' ').trim();

  const trimTokens = [' including ', ' such as ', ' e.g. ', ' e.g., ', ' for example '];
  for (const token of trimTokens) {
    const idx = base.toLowerCase().indexOf(token.trim());
    if (idx > 0) {
      base = base.slice(0, idx).trim();
      break;
    }
  }

  if (base.includes('. ')) {
    base = base.split('. ')[0].trim();
  }

  if (base.length > 90) {
    const commaCut = base.split(',')[0].trim();
    if (commaCut.length >= 40) {
      base = commaCut;
    }
  }

  if (base.length > 90) {
    const andCut = base.split(' and ')[0].trim();
    if (andCut.length >= 40) {
      base = andCut;
    }
  }

  if (base.length > 90) {
    base = `${base.slice(0, 87).trimEnd()}...`;
  }

  return base;
}

function readFrontmatter(filePath) {
  if (!pathExists(filePath)) {
    return { description: '' };
  }
  const content = fs.readFileSync(filePath, 'utf8');
  const lines = content.split(/\r?\n/);
  if (!lines.length || lines[0].trim() !== '---') {
    return { description: '' };
  }

  const data = {};
  for (let i = 1; i < lines.length; i += 1) {
    const line = lines[i];
    if (line.trim() === '---') {
      break;
    }
    if (/^\s/.test(line)) {
      continue;
    }
    const separatorIndex = line.indexOf(':');
    if (separatorIndex === -1) {
      continue;
    }
    const key = line.slice(0, separatorIndex).trim();
    let value = line.slice(separatorIndex + 1).trim();
    if (!value) {
      continue;
    }
    value = unquote(value);
    data[key] = value;
  }

  return { description: data.description || '' };
}

function unquote(value) {
  if (
    (value.startsWith('"') && value.endsWith('"')) ||
    (value.startsWith("'") && value.endsWith("'"))
  ) {
    return value.slice(1, -1);
  }
  return value;
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

async function runGitWithProgress(cwd, args, message) {
  // Show message and run git with full stdio (allows auth prompts, shows progress)
  console.log(`\x1b[33m→\x1b[0m ${message}...`);
  
  const result = spawnSync('git', args, { 
    stdio: 'inherit', 
    cwd: cwd || undefined 
  });
  
  if (result.error) {
    console.log(`\x1b[31m✖\x1b[0m ${message}... error`);
    throw result.error;
  }
  
  if (result.status !== 0) {
    console.log(`\x1b[31m✖\x1b[0m ${message}... failed`);
    throw new Error('git command failed');
  }
  
  console.log(`\x1b[32m✔\x1b[0m ${message}... done`);
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
