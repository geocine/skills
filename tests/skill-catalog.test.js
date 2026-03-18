'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { findSkills, loadSkillsJson, splitRepositoryField } = require('../src/skill-catalog');

function makeTempDir(prefix) {
  return fs.mkdtempSync(path.join(os.tmpdir(), prefix));
}

function writeSkill(repoDir, skillName, content) {
  const skillDir = path.join(repoDir, 'skills', skillName);
  fs.mkdirSync(skillDir, { recursive: true });
  fs.writeFileSync(path.join(skillDir, 'SKILL.md'), content, 'utf8');
}

test('findSkills reads SKILL frontmatter and nested metadata short-description', () => {
  const repoDir = makeTempDir('geocine-skills-catalog-');
  writeSkill(
    repoDir,
    'skill-creator',
    [
      '---',
      'name: skill-creator',
      'description: Guide for creating effective skills.',
      'metadata:',
      '  short-description: Create or update a skill',
      '---',
      '',
      '# Skill Creator',
      '',
    ].join('\n')
  );

  const skills = findSkills(repoDir);

  assert.equal(skills.length, 1);
  assert.equal(skills[0].name, 'skill-creator');
  assert.equal(skills[0].shortDescription, 'Create or update a skill');
});

test('loadSkillsJson takes precedence when the file exists', () => {
  const repoDir = makeTempDir('geocine-skills-catalog-');
  writeSkill(
    repoDir,
    'alpha-skill',
    [
      '---',
      'name: alpha-skill',
      'description: Alpha description.',
      '---',
      '',
      '# Alpha',
      '',
    ].join('\n')
  );

  fs.writeFileSync(
    path.join(repoDir, 'skills.json'),
    JSON.stringify(
      [
        {
          name: 'beta-skill',
          description: 'Beta description',
          shortDescription: 'Beta short',
          repository: 'any',
          path: 'skills/alpha-skill',
        },
      ],
      null,
      2
    ),
    'utf8'
  );

  const fromJson = loadSkillsJson(repoDir);
  const found = findSkills(repoDir);

  assert.equal(fromJson.length, 1);
  assert.equal(found.length, 1);
  assert.equal(found[0].name, 'beta-skill');
  assert.equal(found[0].shortDescription, 'Beta short');
});

test('splitRepositoryField expands comma-separated repositories into unique pills', () => {
  assert.deepEqual(
    splitRepositoryField('device ui, commonrepository, device ui'),
    ['device ui', 'commonrepository']
  );
});

test('splitRepositoryField falls back to any when the field is empty', () => {
  assert.deepEqual(splitRepositoryField(''), ['any']);
  assert.deepEqual(splitRepositoryField(undefined), ['any']);
});
