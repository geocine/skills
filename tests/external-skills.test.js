'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {
  EXTERNAL_SKILLS,
  getExplicitExternalSkills,
  getExternalSkills,
  isExplicitExternalSkillName,
  materializeSkillSources,
} = require('../src/external-skills');

function makeTempDir(prefix) {
  return fs.mkdtempSync(path.join(os.tmpdir(), prefix));
}

test('EXTERNAL_SKILLS registers planpack from its own public repo', () => {
  const planpack = EXTERNAL_SKILLS.find((skill) => skill.name === 'planpack');

  assert.ok(planpack);
  assert.equal(planpack.external.repoUrl, 'https://github.com/geocine/planpack.git');
  assert.equal(planpack.external.ref, 'main');
  assert.equal(planpack.external.path, '.');
  assert.equal(isExplicitExternalSkillName('planpack'), true);
  assert.equal(getExplicitExternalSkills(['planpack']).length, 1);
  assert.equal(
    getExternalSkills().some((skill) => skill.name === 'planpack'),
    true
  );
});

test('materializeSkillSources clones a whole-repo skill to the checkout root', async () => {
  const tempParent = makeTempDir('geocine-skills-external-');
  const [planpack] = getExplicitExternalSkills(['planpack']);
  const cloneArgs = [];

  const prepared = await materializeSkillSources([planpack], {
    tempParentDir: tempParent,
    runGitCommand: (args) => {
      cloneArgs.push(args);
      const dest = args[args.length - 1];
      fs.mkdirSync(dest, { recursive: true });
      fs.writeFileSync(path.join(dest, 'SKILL.md'), '# planpack\n', 'utf8');
      fs.mkdirSync(path.join(dest, 'template'), { recursive: true });
      return { stdout: '' };
    },
  });

  try {
    assert.equal(cloneArgs.length, 1);
    assert.deepEqual(cloneArgs[0].slice(0, 3), ['clone', '--depth', '1']);
    assert.equal(cloneArgs[0].includes('--sparse'), false);
    assert.ok(fs.existsSync(path.join(prepared.skills[0].path, 'SKILL.md')));
    assert.ok(fs.existsSync(path.join(prepared.skills[0].path, 'template')));
  } finally {
    await prepared.cleanup();
  }
});
