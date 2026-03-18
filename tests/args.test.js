'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { parseArgs } = require('../src/args');

test('parseArgs keeps install as the default command', () => {
  const parsed = parseArgs([]);
  assert.equal(parsed.command, '');
  assert.equal(parsed.options.global, false);
  assert.deepEqual(parsed.options.skills, []);
});

test('parseArgs reads install flags and repo override', () => {
  const parsed = parseArgs([
    'install',
    '--skills',
    'alpha,beta',
    '--project',
    'C:\\work\\repo',
    '--repo-url',
    'git@github.com:geocine/skills.git',
    '--details',
    '--force',
  ]);

  assert.equal(parsed.command, 'install');
  assert.deepEqual(parsed.options.skills, ['alpha', 'beta']);
  assert.equal(parsed.options.projectPath, 'C:\\work\\repo');
  assert.equal(parsed.options.repoUrl, 'git@github.com:geocine/skills.git');
  assert.equal(parsed.options.details, true);
  assert.equal(parsed.options.force, true);
});

test('parseArgs supports equals-style flags and aliases', () => {
  const parsed = parseArgs([
    'list',
    '--filter=design',
    '--repo-url=ssh://git@github.com/geocine/skills.git',
    '-y',
  ]);

  assert.equal(parsed.command, 'list');
  assert.equal(parsed.options.filter, 'design');
  assert.equal(parsed.options.repoUrl, 'ssh://git@github.com/geocine/skills.git');
  assert.equal(parsed.options.yes, true);
});

test('parseArgs accepts positional skill names for install and add flows', () => {
  const direct = parseArgs(['frontend-design', '--project']);
  assert.equal(direct.command, 'install');
  assert.deepEqual(direct.options.skills, ['frontend-design']);
  assert.equal(direct.options.projectPath, '');

  const add = parseArgs(['add', 'frontend-design', 'zinc-design-system', '--copy']);
  assert.equal(add.command, 'add');
  assert.deepEqual(add.options.skills, ['frontend-design', 'zinc-design-system']);
  assert.equal(add.options.copy, true);
});
