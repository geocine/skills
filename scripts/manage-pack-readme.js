'use strict';

const fs = require('fs');
const path = require('path');

function getPaths(repoRoot = path.resolve(__dirname, '..')) {
  const tempDir = path.join(repoRoot, '.pack-readme');
  return {
    repoRoot,
    repoReadmePath: path.join(repoRoot, 'README.md'),
    packageReadmePath: path.join(repoRoot, 'src', 'README.md'),
    tempDir,
    backupReadmePath: path.join(tempDir, 'README.md.backup'),
  };
}

function preparePackReadme(repoRoot) {
  const paths = getPaths(repoRoot);
  ensureFile(paths.repoReadmePath);
  ensureFile(paths.packageReadmePath);

  fs.mkdirSync(paths.tempDir, { recursive: true });
  if (!fs.existsSync(paths.backupReadmePath)) {
    fs.copyFileSync(paths.repoReadmePath, paths.backupReadmePath);
  }

  fs.copyFileSync(paths.packageReadmePath, paths.repoReadmePath);
}

function restorePackReadme(repoRoot) {
  const paths = getPaths(repoRoot);
  if (!fs.existsSync(paths.backupReadmePath)) {
    return;
  }

  fs.copyFileSync(paths.backupReadmePath, paths.repoReadmePath);
  fs.rmSync(paths.tempDir, { recursive: true, force: true });
}

function ensureFile(filePath) {
  if (!fs.existsSync(filePath)) {
    throw new Error(`Missing required file: ${filePath}`);
  }
}

function runCli() {
  const command = process.argv[2];

  if (command === 'prepack') {
    preparePackReadme();
    return;
  }

  if (command === 'postpack') {
    restorePackReadme();
    return;
  }

  throw new Error('Expected "prepack" or "postpack".');
}

if (require.main === module) {
  try {
    runCli();
  } catch (error) {
    console.error(error.message || String(error));
    process.exit(1);
  }
}

module.exports = {
  getPaths,
  preparePackReadme,
  restorePackReadme,
};
