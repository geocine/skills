#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const esbuild = require('esbuild');

const repoRoot = path.resolve(__dirname, '..');
const entry = path.join(repoRoot, 'src', 'index.js');
const outFile = path.join(repoRoot, 'bin', 'add-skill.js');

if (!fs.existsSync(entry)) {
  console.error(`Missing entry file: ${entry}`);
  process.exit(1);
}

fs.mkdirSync(path.dirname(outFile), { recursive: true });

esbuild.build({
  entryPoints: [entry],
  bundle: true,
  platform: 'node',
  target: ['node18'],
  outfile: outFile,
  jsx: 'transform',
  loader: { '.js': 'jsx' },
  external: ['ink', 'react'],
  banner: {
    js: [
      '#!/usr/bin/env node',
      '/*',
      ' * This file is generated. Do not edit directly.',
      ' * Edit src/index.js and run `npm run build` to rebuild.',
      ' */'
    ].join('\n')
  },
  logLevel: 'info',
}).then(() => {
  try {
    fs.chmodSync(outFile, 0o755);
  } catch (err) {
    // chmod may fail on some Windows setups; ignore.
  }
}).catch((err) => {
  console.error(err.message || err);
  process.exit(1);
});