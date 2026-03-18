'use strict';

const { spawnSync } = require('child_process');
const path = require('path');
const { DEFAULT_REPO_URL, PRIVATE_REPO_ENV_VAR } = require('./constants');

const inheritedGitConfigCache = new Map();

class GitCommandError extends Error {
  constructor(message, details = {}) {
    super(message);
    this.name = 'GitCommandError';
    this.code = details.code || '';
    this.stderr = details.stderr || '';
    this.stdout = details.stdout || '';
    this.args = details.args || [];
    this.repoUrl = details.repoUrl || '';
    this.isAuthError = Boolean(details.isAuthError);
    this.isMissingGit = Boolean(details.isMissingGit);
  }
}

function runGit(args, options = {}) {
  const commandArgs = [...getInheritedGitConfigArgs(options.gitConfigContextCwd), ...args];
  const result = spawnSync('git', commandArgs, {
    cwd: options.cwd || undefined,
    encoding: 'utf8',
    env: {
      ...process.env,
      GIT_TERMINAL_PROMPT: '0',
      GCM_INTERACTIVE: 'Never',
    },
  });

  if (result.error) {
    const isMissingGit = result.error.code === 'ENOENT';
    throw new GitCommandError(
      isMissingGit ? 'Git is not installed or not available in PATH.' : result.error.message,
      {
        code: result.error.code,
        args: commandArgs,
        isMissingGit,
      }
    );
  }

  if (result.status !== 0) {
    const stderr = (result.stderr || '').trim();
    const stdout = (result.stdout || '').trim();
    throw new GitCommandError(stderr || stdout || 'git command failed', {
      code: String(result.status),
      stderr,
      stdout,
      args: commandArgs,
      repoUrl: options.repoUrl,
      isAuthError: isGitAuthError(stderr || stdout),
    });
  }

  return {
    stdout: (result.stdout || '').trim(),
    stderr: (result.stderr || '').trim(),
  };
}

function getInheritedGitConfigArgs(contextCwd) {
  return getInheritedGitConfigEntries(contextCwd).flatMap(({ key, value }) => ['-c', `${key}=${value}`]);
}

function getInheritedGitConfigEntries(contextCwd) {
  if (!contextCwd) {
    return [];
  }

  const normalizedCwd = path.resolve(contextCwd);
  if (inheritedGitConfigCache.has(normalizedCwd)) {
    return inheritedGitConfigCache.get(normalizedCwd);
  }

  const result = spawnSync(
    'git',
    ['-C', normalizedCwd, 'config', '--get-regexp', '^(core\\.sshcommand|url\\..*\\.insteadof)$'],
    {
      encoding: 'utf8',
      env: {
        ...process.env,
        GIT_TERMINAL_PROMPT: '0',
        GCM_INTERACTIVE: 'Never',
      },
    }
  );

  if (result.error || result.status !== 0) {
    inheritedGitConfigCache.set(normalizedCwd, []);
    return [];
  }

  const entries = [];
  const seen = new Set();
  String(result.stdout || '')
    .split(/\r?\n/)
    .filter(Boolean)
    .forEach((line) => {
      const separatorIndex = line.search(/\s/);
      if (separatorIndex <= 0) {
        return;
      }

      const key = line.slice(0, separatorIndex).trim();
      const value = normalizeInheritedConfigValue(key, line.slice(separatorIndex).trim());
      if (!key || !value) {
        return;
      }

      const entryKey = `${key}\0${value}`;
      if (seen.has(entryKey)) {
        return;
      }

      seen.add(entryKey);
      entries.push({ key, value });
    });

  inheritedGitConfigCache.set(normalizedCwd, entries);
  return entries;
}

function syncInheritedGitConfig(repoCwd, contextCwd) {
  const entries = getInheritedGitConfigEntries(contextCwd);
  if (!repoCwd || entries.length === 0) {
    return;
  }

  const normalizedRepoCwd = path.resolve(repoCwd);
  for (const { key, value } of entries) {
    if (key.endsWith('.insteadof')) {
      const existingValues = getLocalGitConfigValues(normalizedRepoCwd, key);
      if (existingValues.includes(value)) {
        continue;
      }

      setLocalGitConfigValue(normalizedRepoCwd, key, value, { append: true });
      continue;
    }

    setLocalGitConfigValue(normalizedRepoCwd, key, value);
  }
}

function isGitAuthError(message) {
  const text = String(message || '').toLowerCase();
  return [
    'permission denied',
    'authentication failed',
    'could not read username',
    'could not read from remote repository',
    'publickey',
    'repository not found',
    'access denied',
    'not authorized',
  ].some((fragment) => text.includes(fragment));
}

function normalizeInheritedConfigValue(key, value) {
  if (!value) {
    return '';
  }

  if (key === 'core.sshcommand' && /\s/.test(value)) {
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      return value;
    }

    return `"${value}"`;
  }

  return value;
}

function getLocalGitConfigValues(repoCwd, key) {
  const result = spawnSync('git', ['-C', repoCwd, 'config', '--local', '--get-all', key], {
    encoding: 'utf8',
    env: {
      ...process.env,
      GIT_TERMINAL_PROMPT: '0',
      GCM_INTERACTIVE: 'Never',
    },
  });

  if (result.error || result.status !== 0) {
    return [];
  }

  return String(result.stdout || '')
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
}

function setLocalGitConfigValue(repoCwd, key, value, options = {}) {
  const args = ['-C', repoCwd, 'config', '--local'];
  if (options.append) {
    args.push('--add');
  }
  args.push(key, value);

  const result = spawnSync('git', args, {
    encoding: 'utf8',
    env: {
      ...process.env,
      GIT_TERMINAL_PROMPT: '0',
      GCM_INTERACTIVE: 'Never',
    },
  });

  if (result.error) {
    const isMissingGit = result.error.code === 'ENOENT';
    throw new GitCommandError(
      isMissingGit ? 'Git is not installed or not available in PATH.' : result.error.message,
      {
        code: result.error.code,
        args,
        isMissingGit,
      }
    );
  }

  if (result.status !== 0) {
    const stderr = (result.stderr || '').trim();
    const stdout = (result.stdout || '').trim();
    throw new GitCommandError(stderr || stdout || 'git config failed', {
      code: String(result.status),
      stderr,
      stdout,
      args,
    });
  }
}

function formatGitAccessError(repoUrl, error) {
  const repoLabel = repoUrl && repoUrl !== DEFAULT_REPO_URL ? repoUrl : 'the skills repository';

  if (!(error instanceof GitCommandError)) {
    return `Failed to access ${repoLabel}: ${error.message || String(error)}`;
  }

  if (error.isMissingGit) {
    return 'Git is required for skills. Install Git and make sure it is available in PATH.';
  }

  if (error.isAuthError) {
    if (repoUrl && repoUrl !== DEFAULT_REPO_URL) {
      return [
        `Failed to access ${repoLabel}.`,
        'Git could not fetch the requested skill source.',
        `Verify the repository is reachable with: git ls-remote ${repoUrl}`,
        'If the repository is private, configure the required Git credentials before retrying.',
      ].join('\n');
    }

    return [
      `Failed to access ${repoLabel}.`,
      'Git authentication did not succeed.',
      `Use a repo URL you can access via --repo-url or ${PRIVATE_REPO_ENV_VAR}.`,
      'For SSH, verify your key with: ssh -T git@github.com',
      'For HTTPS, configure a credential helper or token before retrying.',
    ].join('\n');
  }

  return `Failed to access ${repoLabel}:\n${error.message}`;
}

module.exports = {
  GitCommandError,
  formatGitAccessError,
  getInheritedGitConfigArgs,
  runGit,
  syncInheritedGitConfig,
};
