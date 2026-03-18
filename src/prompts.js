'use strict';

const { INSTALL_TARGETS } = require('./constants');
const { splitRepositoryField } = require('./skill-catalog');
const {
  cancelSymbol,
  confirmPrompt,
  multiselectPrompt,
  searchMultiselect,
  selectPrompt,
} = require('./search-multiselect');
const { accent, danger, muted, success } = require('./theme');

const STATUS_MARKER = muted('•');

async function promptForSkills(skills, options = {}) {
  const items = skills.map((skill) => ({
    value: skill,
    label: skill.name,
    hint: options.details ? skill.description : skill.shortDescription || skill.description,
    badges: splitRepositoryField(skill.repository),
  }));

  return searchMultiselect({
    message: 'Select skills to install',
    items,
    required: true,
    emptyText: 'No skills match the current filter.',
  });
}

async function promptForTargets() {
  return multiselectPrompt({
    message: 'Choose install targets',
    items: INSTALL_TARGETS.map((target) => ({
      value: target.key,
      label: target.name,
      hint: `${target.folder}/skills`,
    })),
    initialValues: INSTALL_TARGETS.filter((target) => target.key !== 'claude').map((target) => target.key),
    required: true,
    instructions: 'Use arrows to move, space to toggle, a for all, then press enter to confirm.',
  });
}

async function promptForScope() {
  return selectPrompt({
    message: 'Install location',
    items: [
      {
        value: 'global',
        label: 'Global',
        hint: 'Available everywhere on this machine',
      },
      {
        value: 'project',
        label: 'Project',
        hint: 'Available only in the current project folder',
      },
    ],
    required: true,
  });
}

async function promptForInstallMode() {
  return selectPrompt({
    message: 'Installation method',
    items: [
      {
        value: 'symlink',
        label: 'Symlink',
        hint: 'Link each selected target directly to the source skill directory',
      },
      {
        value: 'copy',
        label: 'Copy',
        hint: 'Copy files directly into each selected target',
      },
    ],
    required: true,
  });
}

async function confirmOverwrite() {
  return confirmPrompt({
    message: 'Overwrite existing installed skills?',
    active: 'Overwrite',
    inactive: 'Skip existing',
    initialValue: false,
  });
}

async function createSpinner() {
  return createInlineSpinner();
}

async function intro() {
  console.log(`${STATUS_MARKER} ${muted('skills installer')}`);
}

async function outro(message) {
  console.log(`${STATUS_MARKER} ${success(message)}`);
}

function createInlineSpinner() {
  let activeMessage = '';
  let visible = false;

  const render = (message) => {
    process.stdout.write(`\r\x1b[2K${STATUS_MARKER} ${accent(message)}`);
  };

  const clear = () => {
    if (!visible) {
      return;
    }
    process.stdout.write('\r\x1b[2K');
    visible = false;
  };

  return {
    start(message = '') {
      activeMessage = message;
      visible = true;
      render(activeMessage);
    },
    stop(message = activeMessage, state = 'success') {
      clear();

      const painter = state === 'error' ? danger : success;
      console.log(`${STATUS_MARKER} ${painter(message)}`);
    },
    message(message = '') {
      activeMessage = message;
      if (visible) {
        render(activeMessage);
      } else {
        console.log(`${STATUS_MARKER} ${accent(activeMessage)}`);
      }
    },
  };
}

module.exports = {
  cancelSymbol,
  confirmOverwrite,
  createSpinner,
  intro,
  outro,
  promptForInstallMode,
  promptForScope,
  promptForSkills,
  promptForTargets,
};
