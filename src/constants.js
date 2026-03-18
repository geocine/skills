'use strict';

const os = require('os');
const path = require('path');

const CLI_NAME = 'skills';
const DEFAULT_BRANCH = 'main';
const DEFAULT_REPO_URL = 'git@github.com:geocine/skills.git';
const PRIVATE_REPO_ENV_VAR = 'SKILLS_REPO_URL';
const CACHE_DIR_NAME = '.geocine-skills';
const CACHE_METADATA_FILE = '.geocine-skills-cache.json';
const CACHE_TTL_MS = 6 * 60 * 60 * 1000;

const INSTALL_TARGETS = [
  {
    key: 'agents',
    name: 'GitHub Copilot, Cursor, Codex, OpenCode',
    folder: '.agents',
  },
  {
    key: 'claude',
    name: 'Claude Code',
    folder: '.claude',
  },
];

function userHome() {
  return process.env.USERPROFILE || os.homedir();
}

function getCacheDir(homeDir = userHome()) {
  return path.join(homeDir, CACHE_DIR_NAME);
}

function getCacheMetadataPath(cacheDir) {
  return path.join(cacheDir, CACHE_METADATA_FILE);
}

module.exports = {
  CACHE_DIR_NAME,
  CACHE_METADATA_FILE,
  CACHE_TTL_MS,
  CLI_NAME,
  DEFAULT_BRANCH,
  DEFAULT_REPO_URL,
  INSTALL_TARGETS,
  PRIVATE_REPO_ENV_VAR,
  getCacheDir,
  getCacheMetadataPath,
  userHome,
};
