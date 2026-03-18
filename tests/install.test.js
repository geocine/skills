'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { buildInstallPlan, installSkills } = require('../src/installer');

function makeTempDir(prefix) {
  return fs.mkdtempSync(path.join(os.tmpdir(), prefix));
}

test('installSkills copies files and skips existing targets without force', async () => {
  const tempRoot = makeTempDir('geocine-skills-install-');
  const skillDir = path.join(tempRoot, 'source-skill');

  fs.mkdirSync(path.join(skillDir, 'references'), { recursive: true });
  fs.writeFileSync(path.join(skillDir, 'SKILL.md'), '# Skill\n', 'utf8');
  fs.writeFileSync(path.join(skillDir, 'references', 'note.txt'), 'hello\n', 'utf8');

  const skill = { name: 'demo-skill', path: skillDir };
  const plan = buildInstallPlan({ projectPath: tempRoot }, ['agents'], 'project', 'copy');
  const firstRun = await installSkills([skill], plan, false);
  const installedFile = path.join(tempRoot, '.agents', 'skills', 'demo-skill', 'references', 'note.txt');

  assert.equal(firstRun.length, 1);
  assert.equal(firstRun[0].skipped, false);
  assert.equal(fs.readFileSync(installedFile, 'utf8'), 'hello\n');

  fs.writeFileSync(installedFile, 'changed\n', 'utf8');
  const secondRun = await installSkills([skill], plan, false);
  assert.equal(secondRun[0].skipped, true);
  assert.equal(fs.readFileSync(installedFile, 'utf8'), 'changed\n');

  const forcedRun = await installSkills([skill], plan, true);
  assert.equal(forcedRun[0].skipped, false);
  assert.equal(fs.readFileSync(installedFile, 'utf8'), 'hello\n');
});

test('installSkills symlinks selected targets directly to the source skill directory', async () => {
  const tempRoot = makeTempDir('geocine-skills-install-');
  const skillDir = path.join(tempRoot, 'source-skill');

  fs.mkdirSync(skillDir, { recursive: true });
  fs.writeFileSync(path.join(skillDir, 'SKILL.md'), '# Skill\n', 'utf8');
  fs.writeFileSync(path.join(skillDir, 'payload.txt'), 'link me\n', 'utf8');

  const skill = { name: 'linked-skill', path: skillDir };
  const plan = buildInstallPlan({ projectPath: tempRoot }, ['agents', 'claude'], 'project', 'symlink');
  const results = await installSkills([skill], plan, false);
  const agentsDir = path.join(tempRoot, '.agents', 'skills', 'linked-skill');
  const claudeDir = path.join(tempRoot, '.claude', 'skills', 'linked-skill');

  assert.equal(results.length, 2);
  assert.equal(fs.realpathSync(agentsDir), fs.realpathSync(skillDir));
  assert.equal(fs.realpathSync(claudeDir), fs.realpathSync(skillDir));
  assert.equal(fs.readFileSync(path.join(agentsDir, 'payload.txt'), 'utf8'), 'link me\n');
  assert.equal(fs.readFileSync(path.join(claudeDir, 'payload.txt'), 'utf8'), 'link me\n');
  assert.equal(results.some((result) => result.mode === 'symlink'), true);

  fs.writeFileSync(path.join(skillDir, 'payload.txt'), 'updated through source\n', 'utf8');
  assert.equal(fs.readFileSync(path.join(agentsDir, 'payload.txt'), 'utf8'), 'updated through source\n');
  assert.equal(fs.readFileSync(path.join(claudeDir, 'payload.txt'), 'utf8'), 'updated through source\n');
});

test('installSkills copies external skills even when symlink mode is selected', async () => {
  const tempRoot = makeTempDir('geocine-skills-install-');
  const skillDir = path.join(tempRoot, 'external-source-skill');

  fs.mkdirSync(skillDir, { recursive: true });
  fs.writeFileSync(path.join(skillDir, 'SKILL.md'), '# Skill\n', 'utf8');
  fs.writeFileSync(path.join(skillDir, 'payload.txt'), 'external copy\n', 'utf8');

  const skill = {
    name: 'external-skill',
    path: skillDir,
    external: { repoUrl: 'https://example.com/repo.git' },
  };
  const plan = buildInstallPlan({ projectPath: tempRoot }, ['agents'], 'project', 'symlink');
  const results = await installSkills([skill], plan, false);
  const agentsDir = path.join(tempRoot, '.agents', 'skills', 'external-skill');

  assert.equal(results.length, 1);
  assert.equal(results[0].mode, 'copy');
  assert.equal(fs.readFileSync(path.join(agentsDir, 'payload.txt'), 'utf8'), 'external copy\n');

  fs.writeFileSync(path.join(skillDir, 'payload.txt'), 'changed source\n', 'utf8');
  assert.equal(fs.readFileSync(path.join(agentsDir, 'payload.txt'), 'utf8'), 'external copy\n');
});
