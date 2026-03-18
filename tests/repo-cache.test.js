'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { CACHE_TTL_MS, getCacheMetadataPath } = require('../src/constants');
const { ensureRepoCache, getConfiguredRepoUrl } = require('../src/repo-cache');

function runGit(args, cwd) {
  const gitBin = process.platform === 'win32' ? 'git.exe' : 'git';
  const result = spawnSync(gitBin, args, {
    cwd,
    encoding: 'utf8',
  });

  assert.equal(result.status, 0, result.stderr || result.stdout);
}

function makeTempDir(prefix) {
  return fs.mkdtempSync(path.join(os.tmpdir(), prefix));
}

function createRepo(baseDir, skillName) {
  fs.mkdirSync(baseDir, { recursive: true });
  runGit(['init', '-b', 'main'], baseDir);
  runGit(['config', 'user.name', 'Geocine Skills Test'], baseDir);
  runGit(['config', 'user.email', 'skills@example.com'], baseDir);
  writeSkillFiles(baseDir, skillName, `# ${skillName}\n`);
  commitAll(baseDir, `add ${skillName}`);
}

function writeSkillFiles(repoDir, skillName, skillContent) {
  const skillDir = path.join(repoDir, 'skills', skillName);
  fs.mkdirSync(skillDir, { recursive: true });
  fs.writeFileSync(path.join(skillDir, 'SKILL.md'), skillContent, 'utf8');
}

function commitAll(repoDir, message) {
  runGit(['add', '.'], repoDir);
  runGit(['commit', '-m', message], repoDir);
}

test('ensureRepoCache clones on first use and writes metadata', () => {
  const sourceRepo = makeTempDir('geocine-skills-source-');
  const cacheDir = makeTempDir('geocine-skills-cache-');
  createRepo(sourceRepo, 'alpha-skill');

  fs.rmSync(cacheDir, { recursive: true, force: true });

  const result = ensureRepoCache(
    { repoUrl: sourceRepo },
    { cacheDir, now: 1000 }
  );

  assert.equal(result.status, 'cloned');
  assert.ok(fs.existsSync(path.join(cacheDir, 'skills', 'alpha-skill', 'SKILL.md')));

  const metadata = JSON.parse(fs.readFileSync(getCacheMetadataPath(cacheDir), 'utf8'));
  assert.equal(metadata.repoUrl, sourceRepo);
  assert.equal(metadata.lastFetchedAt, 1000);
});

test('getConfiguredRepoUrl prefers the public env var', () => {
  assert.equal(
    getConfiguredRepoUrl({}, { SKILLS_REPO_URL: 'ssh://override' }),
    'ssh://override'
  );
});

test('ensureRepoCache refreshes stale caches', () => {
  const sourceRepo = makeTempDir('geocine-skills-source-');
  const cacheDir = makeTempDir('geocine-skills-cache-');
  createRepo(sourceRepo, 'alpha-skill');

  fs.rmSync(cacheDir, { recursive: true, force: true });
  ensureRepoCache({ repoUrl: sourceRepo }, { cacheDir, now: 1000 });

  writeSkillFiles(sourceRepo, 'beta-skill', '# beta-skill\n');
  commitAll(sourceRepo, 'add beta-skill');

  const result = ensureRepoCache(
    { repoUrl: sourceRepo },
    { cacheDir, now: 1000 + CACHE_TTL_MS + 1 }
  );

  assert.equal(result.status, 'refreshed');
  assert.ok(fs.existsSync(path.join(cacheDir, 'skills', 'beta-skill', 'SKILL.md')));
});

test('ensureRepoCache respects --no-pull and repo-url changes', () => {
  const sourceRepoA = makeTempDir('geocine-skills-source-a-');
  const sourceRepoB = makeTempDir('geocine-skills-source-b-');
  const cacheDir = makeTempDir('geocine-skills-cache-');
  createRepo(sourceRepoA, 'alpha-skill');
  createRepo(sourceRepoB, 'beta-skill');

  fs.rmSync(cacheDir, { recursive: true, force: true });
  ensureRepoCache({ repoUrl: sourceRepoA }, { cacheDir, now: 1000 });

  writeSkillFiles(sourceRepoA, 'gamma-skill', '# gamma-skill\n');
  commitAll(sourceRepoA, 'add gamma-skill');

  const staleResult = ensureRepoCache(
    { repoUrl: sourceRepoA, noPull: true },
    { cacheDir, now: 1000 + CACHE_TTL_MS + 1 }
  );

  assert.equal(staleResult.status, 'reused');
  assert.equal(fs.existsSync(path.join(cacheDir, 'skills', 'gamma-skill', 'SKILL.md')), false);

  const recloned = ensureRepoCache(
    { repoUrl: sourceRepoB },
    { cacheDir, now: 2000 }
  );

  assert.equal(recloned.status, 'recloned');
  assert.ok(fs.existsSync(path.join(cacheDir, 'skills', 'beta-skill', 'SKILL.md')));
  assert.equal(fs.existsSync(path.join(cacheDir, 'skills', 'alpha-skill', 'SKILL.md')), false);
});
