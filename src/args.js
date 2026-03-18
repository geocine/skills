'use strict';

const KNOWN_COMMANDS = new Set(['install', 'add', 'list', 'update', 'help', 'version']);

function parseArgs(argv) {
  let command = '';
  const options = {
    dest: '',
    global: false,
    projectPath: undefined,
    skills: [],
    all: false,
    copy: false,
    force: false,
    noPull: false,
    yes: false,
    filter: '',
    details: false,
    repoUrl: '',
  };

  const args = [...argv];
  if (args[0] && !args[0].startsWith('-')) {
    const firstToken = args.shift();
    if (KNOWN_COMMANDS.has(firstToken)) {
      command = firstToken;
    } else {
      command = 'install';
      options.skills.push(firstToken);
    }
  }

  while (args.length) {
    const arg = args.shift();
    switch (arg) {
      case '--dest':
        options.dest = args.shift() || '';
        break;
      case '--global':
        options.global = true;
        break;
      case '--project': {
        const next = args[0];
        if (next && !next.startsWith('-')) {
          options.projectPath = args.shift();
        } else {
          options.projectPath = '';
        }
        break;
      }
      case '--skills':
        options.skills = splitList(args.shift() || '');
        break;
      case '--all':
        options.all = true;
        break;
      case '--copy':
        options.copy = true;
        break;
      case '--force':
        options.force = true;
        break;
      case '--no-pull':
        options.noPull = true;
        break;
      case '--yes':
      case '-y':
        options.yes = true;
        break;
      case '--filter':
      case '--search':
        options.filter = args.shift() || '';
        break;
      case '--details':
      case '--full':
        options.details = true;
        break;
      case '--repo-url':
        options.repoUrl = args.shift() || '';
        break;
      case '--help':
      case '-h':
        command = 'help';
        break;
      case '--version':
      case '-v':
        command = 'version';
        break;
      default:
        if (!arg.startsWith('-') && (command === '' || command === 'install' || command === 'add')) {
          options.skills.push(arg);
          break;
        }
        if (arg.startsWith('--skills=')) {
          options.skills = splitList(arg.split('=').slice(1).join('='));
          break;
        }
        if (arg.startsWith('--project=')) {
          options.projectPath = arg.split('=').slice(1).join('=') || '';
          break;
        }
        if (arg.startsWith('--filter=')) {
          options.filter = arg.split('=').slice(1).join('=') || '';
          break;
        }
        if (arg.startsWith('--repo-url=')) {
          options.repoUrl = arg.split('=').slice(1).join('=') || '';
          break;
        }
        break;
    }
  }

  return { command, options };
}

function splitList(value) {
  return String(value)
    .replace(/[; ]/g, ',')
    .split(',')
    .map((entry) => entry.trim())
    .filter(Boolean);
}

module.exports = {
  KNOWN_COMMANDS,
  parseArgs,
  splitList,
};
