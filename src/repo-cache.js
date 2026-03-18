'use strict';

const fs = require('fs');
const path = require('path');
const {
  CACHE_TTL_MS,
  DEFAULT_BRANCH,
  DEFAULT_REPO_URL,
  PRIVATE_REPO_ENV_VAR,
  getCacheDir,
  getCacheMetadataPath,
} = require('./constants');
const { GitCommandError, formatGitAccessError, runGit, syncInheritedGitConfig } = require('./git');

function getConfiguredRepoUrl(options = {}, env = process.env) {
  return options.repoUrl || env[PRIVATE_REPO_ENV_VAR] || DEFAULT_REPO_URL;
}

function readCacheMetadata(cacheDir) {
  const metadataPath = getCacheMetadataPath(cacheDir);
  try {
    const raw = fs.readFileSync(metadataPath, 'utf8');
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') {
      return null;
    }
    return {
      repoUrl: typeof parsed.repoUrl === 'string' ? parsed.repoUrl : '',
      branch: typeof parsed.branch === 'string' ? parsed.branch : DEFAULT_BRANCH,
      lastFetchedAt: Number.isFinite(parsed.lastFetchedAt) ? parsed.lastFetchedAt : 0,
    };
  } catch {
    return null;
  }
}

function writeCacheMetadata(cacheDir, metadata) {
  const metadataPath = getCacheMetadataPath(cacheDir);
  fs.mkdirSync(cacheDir, { recursive: true });
  fs.writeFileSync(metadataPath, `${JSON.stringify(metadata, null, 2)}\n`, 'utf8');
}

function isCacheStale(metadata, now = Date.now()) {
  if (!metadata || !metadata.lastFetchedAt) {
    return true;
  }
  return now - metadata.lastFetchedAt >= CACHE_TTL_MS;
}

function dirHasSkillEntries(base) {
  if (!isDirectory(base)) {
    return false;
  }
  const entries = fs.readdirSync(base, { withFileTypes: true });
  return entries.some(
    (entry) => entry.isDirectory() && fs.existsSync(path.join(base, entry.name, 'SKILL.md'))
  );
}

function dirHasSkills(root) {
  return dirHasSkillEntries(path.join(root, 'skills')) || dirHasSkillEntries(root);
}

function dirHasRepoMarkers(root) {
  if (fs.existsSync(path.join(root, 'skills.json'))) {
    return true;
  }

  const pkgPath = path.join(root, 'package.json');
  if (fs.existsSync(pkgPath)) {
    try {
      const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
      if (pkg && pkg.name === '@geocine/skills') {
        return true;
      }
    } catch {
      return false;
    }
  }

  return fs.existsSync(path.join(root, 'src', 'skills.js'));
}

function findLocalRepoRoot(startDir) {
  let dir = path.resolve(startDir);

  while (true) {
    if (dirHasSkills(dir) && dirHasRepoMarkers(dir)) {
      return dir;
    }

    const parent = path.dirname(dir);
    if (parent === dir) {
      return null;
    }
    dir = parent;
  }
}

function ensureRepoCache(options = {}, deps = {}) {
  const cacheDir = deps.cacheDir || getCacheDir(deps.homeDir);
  const gitConfigContextCwd = deps.gitConfigContextCwd || process.cwd();
  const repoUrl = options.repoUrl || DEFAULT_REPO_URL;
  const branch = options.branch || DEFAULT_BRANCH;
  const now = deps.now || Date.now();
  const logger = deps.logger || null;
  const forceRefresh = Boolean(options.forceRefresh);
  const noPull = Boolean(options.noPull);

  const metadata = readCacheMetadata(cacheDir);
  const gitDir = path.join(cacheDir, '.git');
  const hasGitRepo = isDirectory(gitDir);
  const remoteUrl = hasGitRepo ? readOriginUrl(cacheDir) : '';

  if (!hasGitRepo) {
    recreateCacheDir(cacheDir);
    cloneRepo(cacheDir, repoUrl, branch, gitConfigContextCwd);
    const nextMetadata = { repoUrl, branch, lastFetchedAt: now };
    writeCacheMetadata(cacheDir, nextMetadata);
    return { path: cacheDir, status: 'cloned', metadata: nextMetadata };
  }

  if ((metadata && metadata.repoUrl && metadata.repoUrl !== repoUrl) || (remoteUrl && remoteUrl !== repoUrl)) {
    recreateCacheDir(cacheDir);
    cloneRepo(cacheDir, repoUrl, branch, gitConfigContextCwd);
    const nextMetadata = { repoUrl, branch, lastFetchedAt: now };
    writeCacheMetadata(cacheDir, nextMetadata);
    return { path: cacheDir, status: 'recloned', metadata: nextMetadata };
  }

  if (forceRefresh) {
    refreshRepo(cacheDir, repoUrl, branch, gitConfigContextCwd);
    const nextMetadata = { repoUrl, branch, lastFetchedAt: now };
    writeCacheMetadata(cacheDir, nextMetadata);
    return { path: cacheDir, status: 'refreshed', metadata: nextMetadata };
  }

  if (noPull) {
    return {
      path: cacheDir,
      status: 'reused',
      metadata: metadata || { repoUrl, branch, lastFetchedAt: 0 },
    };
  }

  if (!isCacheStale(metadata, now)) {
    return { path: cacheDir, status: 'reused', metadata };
  }

  try {
    refreshRepo(cacheDir, repoUrl, branch, gitConfigContextCwd);
    const nextMetadata = { repoUrl, branch, lastFetchedAt: now };
    writeCacheMetadata(cacheDir, nextMetadata);
    return { path: cacheDir, status: 'refreshed', metadata: nextMetadata };
  } catch (error) {
    if (!(error instanceof GitCommandError)) {
      throw error;
    }

    if (logger && typeof logger.warn === 'function') {
      logger.warn(
        `${formatGitAccessError(repoUrl, error)}\nUsing the existing local cache at ${cacheDir}.`
      );
    }

    return {
      path: cacheDir,
      status: 'stale',
      metadata: metadata || { repoUrl, branch, lastFetchedAt: 0 },
      warning: error,
    };
  }
}

function resolveRepoRoot(options = {}, deps = {}) {
  const cwd = deps.cwd || process.cwd();
  const gitConfigContextCwd = deps.gitConfigContextCwd || cwd;
  const preferLocal = options.preferLocal !== false;
  const env = deps.env || process.env;
  const repoUrl = getConfiguredRepoUrl(options, env);

  if (preferLocal && !options.repoUrl && !env[PRIVATE_REPO_ENV_VAR]) {
    const localRepoRoot = findLocalRepoRoot(cwd);
    if (localRepoRoot) {
      return { path: localRepoRoot, status: 'local', repoUrl: '' };
    }
  }

  const cacheResult = ensureRepoCache(
    {
      repoUrl,
      branch: options.branch || DEFAULT_BRANCH,
      noPull: options.noPull,
      forceRefresh: options.forceRefresh,
    },
    { ...deps, gitConfigContextCwd }
  );

  return {
    path: cacheResult.path,
    status: cacheResult.status,
    repoUrl,
    warning: cacheResult.warning,
  };
}

function cloneRepo(cacheDir, repoUrl, branch, gitConfigContextCwd) {
  runGit(['clone', '--depth', '1', '--branch', branch, repoUrl, cacheDir], {
    repoUrl,
    gitConfigContextCwd,
  });
  syncInheritedGitConfig(cacheDir, gitConfigContextCwd);
}

function refreshRepo(cacheDir, repoUrl, branch, gitConfigContextCwd) {
  syncInheritedGitConfig(cacheDir, gitConfigContextCwd);
  runGit(['fetch', '--depth', '1', 'origin', branch], {
    cwd: cacheDir,
    repoUrl,
    gitConfigContextCwd,
  });
  runGit(['reset', '--hard', 'FETCH_HEAD'], {
    cwd: cacheDir,
    repoUrl,
    gitConfigContextCwd,
  });
  runGit(['clean', '-fd', '-e', path.basename(getCacheMetadataPath(cacheDir))], {
    cwd: cacheDir,
    repoUrl,
    gitConfigContextCwd,
  });
}

function readOriginUrl(cacheDir) {
  try {
    const result = runGit(['config', '--get', 'remote.origin.url'], { cwd: cacheDir });
    return result.stdout || '';
  } catch {
    return '';
  }
}

function recreateCacheDir(cacheDir) {
  fs.rmSync(cacheDir, { recursive: true, force: true });
  fs.mkdirSync(path.dirname(cacheDir), { recursive: true });
}

function isDirectory(targetPath) {
  try {
    return fs.statSync(targetPath).isDirectory();
  } catch {
    return false;
  }
}

module.exports = {
  dirHasRepoMarkers,
  dirHasSkillEntries,
  ensureRepoCache,
  findLocalRepoRoot,
  getConfiguredRepoUrl,
  isCacheStale,
  readCacheMetadata,
  resolveRepoRoot,
  writeCacheMetadata,
};
