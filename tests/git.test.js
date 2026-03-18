'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {
  GitCommandError,
  formatGitAccessError,
  getInheritedGitConfigArgs,
  syncInheritedGitConfig,
} = require('../src/git');

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

test('formatGitAccessError uses external repo guidance for non-default repos', () => {
  const error = new GitCommandError('authentication failed', {
    repoUrl: 'https://github.com/example/skills.git',
    isAuthError: true,
  });

  const message = formatGitAccessError('https://github.com/example/skills.git', error);

  assert.equal(message.includes('git ls-remote https://github.com/example/skills.git'), true);
  assert.equal(message.includes('ssh -T git@github.com'), false);
});

test('formatGitAccessError keeps the default repo label generic and references GitHub SSH', () => {
  const error = new GitCommandError('authentication failed', {
    repoUrl: 'git@github.com:geocine/skills.git',
    isAuthError: true,
  });

  const message = formatGitAccessError('git@github.com:geocine/skills.git', error);

  assert.equal(message.includes('skills repository'), true);
  assert.equal(message.includes('ssh -T git@github.com'), true);
  assert.equal(/bitbucket/i.test(message), false);
});

test('getInheritedGitConfigArgs carries repo-scoped ssh and insteadOf settings', () => {
  const repoDir = makeTempDir('geocine-skills-git-config-');

  runGit(['init', '-b', 'main'], repoDir);
  runGit(['config', 'core.sshCommand', '"C:/Program Files/Git/usr/bin/ssh.exe"'], repoDir);
  runGit(
    ['config', 'url.ssh://git@github-mirror/.insteadOf', 'git@github.com:'],
    repoDir
  );

  const args = getInheritedGitConfigArgs(repoDir);

  assert.equal(args.includes("core.sshcommand='C:/Program Files/Git/usr/bin/ssh.exe'"), true);
  assert.equal(args.includes('url.ssh://git@github-mirror/.insteadof=git@github.com:'), true);
});

test('syncInheritedGitConfig writes inherited repo-scoped config into the cache repo', () => {
  const contextRepoDir = makeTempDir('geocine-skills-context-repo-');
  const cacheRepoDir = makeTempDir('geocine-skills-cache-repo-');

  runGit(['init', '-b', 'main'], contextRepoDir);
  runGit(['config', 'core.sshCommand', '"C:/Program Files/Git/usr/bin/ssh.exe"'], contextRepoDir);
  runGit(
    ['config', '--add', 'url.ssh://git@github-mirror/.insteadOf', 'git@github.com:'],
    contextRepoDir
  );

  runGit(['init', '-b', 'main'], cacheRepoDir);
  syncInheritedGitConfig(cacheRepoDir, contextRepoDir);

  const sshCommand = spawnSync(
    process.platform === 'win32' ? 'git.exe' : 'git',
    ['-C', cacheRepoDir, 'config', '--local', '--get', 'core.sshCommand'],
    { encoding: 'utf8' }
  );
  const insteadOf = spawnSync(
    process.platform === 'win32' ? 'git.exe' : 'git',
    ['-C', cacheRepoDir, 'config', '--local', '--get-all', 'url.ssh://git@github-mirror/.insteadOf'],
    { encoding: 'utf8' }
  );

  assert.equal(sshCommand.status, 0, sshCommand.stderr || sshCommand.stdout);
  assert.equal(insteadOf.status, 0, insteadOf.stderr || insteadOf.stdout);
  assert.equal(sshCommand.stdout.includes('C:/Program Files/Git/usr/bin/ssh.exe'), true);
  assert.equal(insteadOf.stdout.includes('git@github.com:'), true);
});
