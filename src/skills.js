'use strict';

const { readFileSync } = require('fs');
const path = require('path');
const { parseArgs } = require('./args');
const {
  CLI_NAME,
  DEFAULT_BRANCH,
  DEFAULT_REPO_URL,
  PRIVATE_REPO_ENV_VAR,
} = require('./constants');
const { formatGitAccessError } = require('./git');
const { buildInstallPlan, hasExistingSkills, installSkills } = require('./installer');
const {
  cancelSymbol,
  confirmOverwrite,
  createSpinner,
  intro,
  outro,
  promptForInstallMode,
  promptForScope,
  promptForSkills,
  promptForTargets,
} = require('./prompts');
const { getConfiguredRepoUrl, resolveRepoRoot } = require('./repo-cache');
const { getExplicitExternalSkills, getExternalSkills, materializeSkillSources } = require('./external-skills');
const { applyListFilter, filterSkillsByName, findSkills } = require('./skill-catalog');
const { accent, danger, muted, strong, success, warm } = require('./theme');

function usage() {
  console.log(`${CLI_NAME}`);
  console.log('');
  console.log('Commands:');
  console.log('  install   Install skills (default)');
  console.log('  add       Alias for install');
  console.log('  list      List available skills');
  console.log('  update    Refresh the local skills cache');
  console.log('  help      Show this help');
  console.log('');
  console.log('Install options:');
  console.log('  --dest <path>        Install into a single destination');
  console.log('  --global             Install to user-level locations');
  console.log('  --project [path]     Install to project-level locations (default: current directory)');
  console.log('  [skill ...]          Install one or more skills by positional name');
  console.log('  --skills <list>      Comma list of skill names to install');
  console.log('  --all                Install all skills');
  console.log('  --copy               Copy files instead of symlinking targets to the source skill directory');
  console.log('  --force              Overwrite existing skills');
  console.log('  --no-pull            Use the local cache as-is');
  console.log('  --yes, -y            Skip prompts (defaults to all skills + global + .agents only)');
  console.log('  --filter <text>      Filter skills by name, description, or repository');
  console.log('  --details            Show full descriptions');
  console.log('  --repo-url <git-url> Override the skills repo URL');
  console.log('');
  console.log('List options:');
  console.log('  --filter <text>      Filter skills by name, description, or repository');
  console.log('  --details            Show full descriptions');
  console.log('  --repo-url <git-url> Override the skills repo URL');
  console.log('');
  console.log('Environment:');
  console.log(`  ${PRIVATE_REPO_ENV_VAR}   Override the skills repo URL`);
  console.log('');
  console.log('Examples:');
  console.log('  npx -y @geocine/skills');
  console.log('  npx -y @geocine/skills frontend-design --project');
  console.log('  npx -y @geocine/skills skill-creator --global');
  console.log('  npx -y @geocine/skills install frontend-design --project');
  console.log('  npx -y @geocine/skills add frontend-design --project');
  console.log('  npx -y @geocine/skills list --filter design');
  console.log('  npx -y @geocine/skills install --skills frontend-design --project');
  console.log('  npx -y @geocine/skills update');
}

async function main() {
  const { command, options } = parseArgs(process.argv.slice(2));
  const effectiveCommand = command || 'install';

  switch (effectiveCommand) {
    case 'install':
    case 'add':
      await runInstall(options);
      break;
    case 'list':
      await runList(options);
      break;
    case 'update':
      await runUpdate(options);
      break;
    case 'help':
      usage();
      break;
    case 'version':
      console.log(getVersion());
      break;
    default:
      console.error(`Unknown command: ${effectiveCommand}`);
      usage();
      process.exitCode = 1;
  }
}

async function runInstall(options) {
  const interactive = process.stdin.isTTY && process.stdout.isTTY;
  const spinner = interactive ? await createSpinner() : null;
  let preparedSkills = null;

  try {
    if (interactive && !options.yes) {
      await intro();
    }

    const explicitExternalSkills = getExplicitExternalSkills(options.skills);
    const explicitExternalNames = new Set(
      explicitExternalSkills.map((skill) => skill.name.toLowerCase())
    );
    const onlyExplicitExternalSkills =
      options.skills.length > 0 &&
      options.skills.every((skillName) => explicitExternalNames.has(String(skillName).toLowerCase()));

    let availableSkills = explicitExternalSkills;
    if (!onlyExplicitExternalSkills) {
      const repoRoot = await withSpinner(spinner, 'Resolving skills repo', () =>
        resolveRepoRoot({ ...options, preferLocal: true })
      );
      logRepoStatus(repoRoot, options);

      const skills = await withSpinner(spinner, 'Loading skills', () =>
        loadAvailableSkills(repoRoot.path)
      );
      availableSkills = mergeExplicitSkills(skills, explicitExternalSkills);
    }

    const filteredSkills = applyListFilter(availableSkills, options);
    if (options.filter && !filteredSkills.length) {
      throw new Error('No skills match the current filter.');
    }

    const selectedSkills = await resolveSelectedSkills(filteredSkills, options, interactive);
    const scope = await resolveInstallScope(options, interactive);
    const targetKeys = await resolveTargetKeys(options, interactive);
    const installMode = await resolveInstallMode(options, targetKeys, interactive);
    const installPlan = buildInstallPlan(options, targetKeys, scope, installMode);

    let force = options.force;
    if (!force && hasExistingSkills(installPlan, selectedSkills)) {
      if (!interactive || options.yes) {
        console.log(
          warm('Some skills already exist and will be skipped. Use --force to overwrite them.')
        );
      } else {
        const overwrite = await confirmOverwrite();
        if (overwrite === cancelSymbol) {
          cancel();
          return;
        }
        force = overwrite;
      }
    }

    preparedSkills = await withSpinner(spinner, 'Preparing selected skills', () =>
      materializeSkillSources(selectedSkills)
    );

    const results = await withSpinner(spinner, 'Installing skills', () =>
      installSkills(preparedSkills.skills, installPlan, force)
    );

    printInstallResults(results);
    if (interactive && !options.yes) {
      await outro('Installation complete. Restart your editor to load new skills.');
    } else {
      console.log(success('Done. Restart your editor to load new skills.'));
    }
  } catch (error) {
    handleRunError(options, error);
  } finally {
    if (preparedSkills) {
      await preparedSkills.cleanup();
    }
  }
}

function loadAvailableSkills(repoPath) {
  return mergeExplicitSkills(findSkills(repoPath), getExternalSkills());
}

function mergeExplicitSkills(skills, explicitSkills) {
  if (!explicitSkills.length) {
    return skills;
  }

  const merged = new Map(skills.map((skill) => [skill.name.toLowerCase(), skill]));
  explicitSkills.forEach((skill) => {
    merged.set(skill.name.toLowerCase(), skill);
  });
  return Array.from(merged.values()).sort((left, right) => left.name.localeCompare(right.name));
}

async function runList(options) {
  const spinner = process.stdout.isTTY ? await createSpinner() : null;

  try {
    const repoRoot = await withSpinner(spinner, 'Resolving skills repo', () =>
      resolveRepoRoot({ ...options, preferLocal: true })
    );
    logRepoStatus(repoRoot, options);

    let skills = await withSpinner(spinner, 'Loading skills', () => loadAvailableSkills(repoRoot.path));
    skills = applyListFilter(skills, options);

    if (!skills.length) {
      console.log(muted('No skills found.'));
      return;
    }

    console.log(strong('Available skills:'));
    for (const skill of skills) {
      const description = options.details ? skill.description : skill.shortDescription || skill.description;
      const repository = skill.repository || 'any';
      const suffix = description ? ` - ${description}` : '';
      console.log(` ${accent('>')} ${strong(skill.name)}${muted(suffix ? suffix : '')} ${warm(`[${repository}]`)}`);
    }
  } catch (error) {
    handleRunError(options, error);
  }
}

async function runUpdate(options) {
  const spinner = process.stdout.isTTY ? await createSpinner() : null;

  try {
    await withSpinner(spinner, 'Refreshing skills cache', () =>
      resolveRepoRoot({
        ...options,
        repoUrl: getConfiguredRepoUrl(options),
        branch: DEFAULT_BRANCH,
        forceRefresh: true,
        preferLocal: false,
      })
    );
    console.log(success('Skills cache refreshed.'));
  } catch (error) {
    handleRunError(options, error);
  }
}

async function resolveSelectedSkills(skills, options, interactive) {
  if (options.all || options.yes) {
    return skills;
  }

  if (options.skills.length) {
    return filterSkillsByName(skills, options.skills);
  }

  if (skills.length === 1) {
    return skills;
  }

  if (!interactive) {
    throw new Error(
      'Interactive skill selection is unavailable without a TTY. Use --skills, --all, or --yes.'
    );
  }

  const selected = await promptForSkills(skills, options);
  if (selected === cancelSymbol) {
    cancel();
    process.exit(0);
  }

  return selected;
}

async function resolveTargetKeys(options, interactive) {
  if (options.dest) {
    return [];
  }

  if (options.yes || !interactive) {
    return ['agents'];
  }

  const selected = await promptForTargets();
  if (selected === cancelSymbol) {
    cancel();
    process.exit(0);
  }

  return selected;
}

async function resolveInstallScope(options, interactive) {
  if (options.dest) {
    return 'dest';
  }
  if (options.global) {
    return 'global';
  }
  if (options.projectPath !== undefined) {
    return 'project';
  }
  if (options.yes) {
    return 'global';
  }
  if (!interactive) {
    throw new Error('Install scope requires a TTY. Use --global, --project, --dest, or --yes.');
  }

  const scope = await promptForScope();
  if (scope === cancelSymbol) {
    cancel();
    process.exit(0);
  }
  return scope;
}

async function resolveInstallMode(options, targetKeys, interactive) {
  if (options.dest || options.copy) {
    return 'copy';
  }

  const needsChoice = targetKeys.includes('claude');
  if (!needsChoice || options.yes || !interactive) {
    return 'symlink';
  }

  const installMode = await promptForInstallMode();
  if (installMode === cancelSymbol) {
    cancel();
    process.exit(0);
  }
  return installMode;
}

function printInstallResults(results) {
  const installed = results.filter((result) => !result.skipped);
  const skipped = results.filter((result) => result.skipped);

  if (installed.length) {
    console.log(success(`Installed ${installed.length} target${installed.length === 1 ? '' : 's'}:`));
    installed.forEach((result) => {
      console.log(`  ${accent('>')} ${strong(result.skill)} ${warm(`[${formatResultMode(result)}]`)} ${muted(`-> ${result.path}`)}`);
    });
  }

  if (skipped.length) {
    console.log(warm(`Skipped ${skipped.length} existing target${skipped.length === 1 ? '' : 's'}:`));
    skipped.forEach((result) => {
      console.log(`  ${accent('>')} ${strong(result.skill)} ${warm(`[${formatResultMode(result)}]`)} ${muted(`-> ${result.path}`)}`);
    });
  }
}

function formatResultMode(result) {
  if (result.symlinkFailed) {
    return 'copy-fallback';
  }
  return result.mode || 'copy';
}

function logRepoStatus(repoRoot, options) {
  if (repoRoot.status === 'local') {
    printDetailLine(`Using the local skills repo at ${repoRoot.path}`);
    return;
  }

  const repoUrl = repoRoot.repoUrl || getConfiguredRepoUrl(options);
  const repoLabel = repoUrl && repoUrl !== DEFAULT_REPO_URL ? repoUrl : 'the skills repo';
  switch (repoRoot.status) {
    case 'cloned':
      printDetailLine(`Cloned ${repoLabel}.`);
      break;
    case 'recloned':
      printDetailLine(`Recreated the cached ${repoLabel}.`);
      break;
    case 'refreshed':
      printDetailLine('Refreshed the cached skills repo.');
      break;
    case 'stale':
      printDetailLine('Using the existing cached skills repo because refresh failed.', warm);
      break;
    default:
      printDetailLine('Using the existing cached skills repo.');
      break;
  }
}

function printDetailLine(message, tone = muted) {
  console.log(`${muted('-')} ${tone(message)}`);
}

async function withSpinner(spinner, message, action) {
  if (spinner) {
    spinner.start(message);
  }
  try {
    const result = await action();
    if (spinner) {
      spinner.stop(message, 'success');
    }
    return result;
  } catch (error) {
    if (spinner) {
      spinner.stop(message, 'error');
    }
    throw error;
  }
}

function handleRunError(options, error) {
  const repoUrl =
    error && typeof error === 'object' && typeof error.repoUrl === 'string' && error.repoUrl
      ? error.repoUrl
      : getConfiguredRepoUrl(options);
  const message =
    error && typeof error === 'object' && error.isAuthError !== undefined
      ? formatGitAccessError(repoUrl, error)
      : error.message || String(error);
  console.error(danger(`Error: ${message}`));
  process.exitCode = 1;
}

function cancel() {}

function getVersion() {
  try {
    const pkgPath = path.join(__dirname, '..', 'package.json');
    const pkg = JSON.parse(readFileSync(pkgPath, 'utf8'));
    return pkg.version || '0.0.0';
  } catch {
    return '0.0.0';
  }
}

main().catch((error) => {
  console.error(danger(`Error: ${error.message || String(error)}`));
  process.exit(1);
});
