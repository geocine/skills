'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const zlib = require('node:zlib');

const repoRoot = path.join(__dirname, '..');
const builtCliPath = path.join(repoRoot, 'bin', 'skills.js');
const repoReadmePath = path.join(repoRoot, 'README.md');
const packageReadmePath = path.join(repoRoot, 'src', 'README.md');

function runNodeScript(args) {
  return spawnSync(process.execPath, args, {
    cwd: repoRoot,
    encoding: 'utf8',
  });
}

test('bundled CLI does not expose Synapse or Bitbucket identifiers', () => {
  const buildResult = runNodeScript(['scripts/bundle-cli.js']);
  assert.equal(
    buildResult.status,
    0,
    buildResult.error ? buildResult.error.message : buildResult.stderr || buildResult.stdout
  );

  const bundledCli = fs.readFileSync(builtCliPath, 'utf8');
  assert.equal(/synapse/i.test(bundledCli), false);
  assert.equal(/bitbucket/i.test(bundledCli), false);
});

test('npm pack uses the package README and restores the repo README afterwards', () => {
  const buildResult = runNodeScript(['scripts/bundle-cli.js']);
  assert.equal(
    buildResult.status,
    0,
    buildResult.error ? buildResult.error.message : buildResult.stderr || buildResult.stdout
  );

  const originalRepoReadme = fs.readFileSync(repoReadmePath, 'utf8');
  const packageReadme = fs.readFileSync(packageReadmePath, 'utf8');
  const result =
    process.platform === 'win32'
      ? spawnSync(process.env.ComSpec || 'cmd.exe', ['/d', '/s', '/c', 'npm.cmd pack --json'], {
          cwd: repoRoot,
          encoding: 'utf8',
        })
      : spawnSync('npm', ['pack', '--json'], {
          cwd: repoRoot,
          encoding: 'utf8',
        });

  assert.equal(result.status, 0, result.error ? result.error.message : result.stderr || result.stdout);
  const output = JSON.parse(result.stdout);
  const tarballName = output[0].filename;
  const files = output[0].files.map((entry) => entry.path).sort();
  const tarballPath = path.join(repoRoot, tarballName);

  try {
    const packedReadme = extractTarEntry(fs.readFileSync(tarballPath), 'package/README.md');
    assert.equal(packedReadme, packageReadme);
    assert.equal(fs.readFileSync(repoReadmePath, 'utf8'), originalRepoReadme);
  } finally {
    fs.rmSync(tarballPath, { force: true });
  }

  assert.equal(files.includes('README.md'), true);
  assert.equal(files.includes('bin/skills.js'), true);
  assert.equal(files.includes('package.json'), true);
});

function extractTarEntry(tgzBuffer, entryName) {
  const tarBuffer = zlib.gunzipSync(tgzBuffer);
  let offset = 0;

  while (offset + 512 <= tarBuffer.length) {
    const header = tarBuffer.subarray(offset, offset + 512);
    const name = header.subarray(0, 100).toString('utf8').replace(/\0.*$/, '');

    if (!name) {
      break;
    }

    const sizeField = header.subarray(124, 136).toString('utf8').replace(/\0.*$/, '').trim();
    const size = sizeField ? parseInt(sizeField, 8) : 0;
    const start = offset + 512;
    const end = start + size;

    if (name === entryName) {
      return tarBuffer.subarray(start, end).toString('utf8');
    }

    offset = start + Math.ceil(size / 512) * 512;
  }

  throw new Error(`Missing tar entry: ${entryName}`);
}
