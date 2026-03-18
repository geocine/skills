'use strict';

const readline = require('readline');
const { Writable } = require('stream');
const { accent, danger, highlightMatch, muted, strong, warm } = require('./theme');

const RAIL = muted('│');
const RAIL_END = muted('└');
const HEADER_MARKER = muted('•');
const ACTIVE_CURSOR = accent('>');
const ACTIVE_DOT = accent('●');
const INACTIVE_DOT = muted('○');
const cancelSymbol = Symbol('cancel');
const ANSI_PATTERN = /\x1b\[[0-9;]*m/g;

const silentOutput = new Writable({
  write(_chunk, _encoding, callback) {
    callback();
  },
});

async function searchMultiselect(options) {
  return runListPrompt({
    ...options,
    searchable: true,
    multiple: true,
  });
}

async function multiselectPrompt(options) {
  return runListPrompt({
    ...options,
    multiple: true,
  });
}

async function selectPrompt(options) {
  return runListPrompt(options);
}

async function confirmPrompt(options) {
  return selectPrompt({
    message: options.message,
    items: [
      { value: true, label: options.active || 'Yes' },
      { value: false, label: options.inactive || 'No' },
    ],
    initialValue: options.initialValue ? true : false,
    instructions: 'Use arrows to choose, then press enter to confirm.',
    emptyText: 'No choices available.',
  });
}

function summarizeLabels(labels) {
  if (!labels.length) {
    return muted('(none)');
  }

  if (labels.length <= 3) {
    return labels.join(', ');
  }

  return `${labels.slice(0, 3).join(', ')} +${labels.length - 3} more`;
}

async function runListPrompt(options) {
  const {
    message,
    items,
    maxVisible = 8,
    required = false,
    searchable = false,
    multiple = false,
    initialValues = [],
    initialValue,
    instructions = '',
    emptyText = 'No options available.',
  } = options;

  if (!process.stdin.isTTY || !process.stdout.isTTY || typeof process.stdin.setRawMode !== 'function') {
    throw new Error('Interactive selection requires a TTY terminal.');
  }

  return new Promise((resolve) => {
    const rl = readline.createInterface({
      input: process.stdin,
      output: silentOutput,
      terminal: false,
    });

    process.stdin.setRawMode(true);
    readline.emitKeypressEvents(process.stdin, rl);

    let query = '';
    let cursor = 0;
    let lastHeight = 0;
    let errorMessage = '';
    const selected = new Set(multiple ? initialValues : []);

    const defaultIndex = initialValue === undefined
      ? 0
      : Math.max(items.findIndex((item) => item.value === initialValue), 0);
    cursor = defaultIndex;

    const filterItems = () => {
      if (!searchable) {
        return items;
      }

      const normalized = query.toLowerCase();
      if (!normalized) {
        return items;
      }

      return items.filter((item) =>
        [item.label, item.hint]
          .filter(Boolean)
          .some((field) => String(field).toLowerCase().includes(normalized))
      );
    };

    const syncCursor = () => {
      const filtered = filterItems();
      if (!filtered.length) {
        cursor = 0;
        return filtered;
      }

      cursor = Math.max(0, Math.min(cursor, filtered.length - 1));
      return filtered;
    };

    const clear = () => {
      if (!lastHeight) {
        return;
      }

      process.stdout.write(`\x1b[${lastHeight}A`);
      for (let index = 0; index < lastHeight; index += 1) {
        process.stdout.write('\x1b[2K\x1b[1B');
      }
      process.stdout.write(`\x1b[${lastHeight}A`);
    };

    const measureRenderedHeight = (lines) => {
      const columns = Math.max(process.stdout.columns || 80, 1);
      return lines.reduce((total, line) => {
        const visible = String(line || '').replace(ANSI_PATTERN, '');
        return total + Math.max(1, Math.ceil(visible.length / columns));
      }, 0);
    };

    const renderInstructions = () => {
      if (instructions) {
        return muted(instructions);
      }

      const parts = [];
      if (searchable) {
        parts.push('type to filter');
      }
      parts.push('arrows to move');
      if (multiple) {
        parts.push('space to toggle');
        parts.push('a all');
      }
      parts.push(multiple ? 'enter confirm' : 'enter select');
      parts.push('esc cancel');
      return muted(parts.join(' | '));
    };

    const withRail = (content = '') => (content ? `${RAIL}  ${content}` : RAIL);
    const withBranch = (content = '') => (content ? `${RAIL_END} ${content}` : RAIL_END);

    const renderBadge = (badge, activeQuery) => {
      const label = highlightMatch(badge, activeQuery, warm);
      return `${accent('[')}${label}${accent(']')}`;
    };

    const renderRow = (item, isActive, isSelected, activeQuery) => {
      const label = highlightMatch(
        item.label,
        activeQuery,
        isActive ? (value) => strong(value) : (value) => muted(value)
      );
      const checkbox = multiple
        ? isSelected ? ACTIVE_DOT : INACTIVE_DOT
        : isActive ? ACTIVE_DOT : INACTIVE_DOT;
      const cursorMark = isActive ? ACTIVE_CURSOR : ' ';
      return withRail(`${cursorMark} ${checkbox} ${label}`);
    };

    const renderDetails = (item, isActive, activeQuery) => {
      const badges = Array.isArray(item.badges) ? item.badges : [];
      if (!item.hint && !badges.length) {
        return [];
      }

      const lines = [];
      if (badges.length) {
        lines.push(withRail(`    ${badges.map((badge) => renderBadge(badge, activeQuery)).join(' ')}`));
      }
      if (item.hint) {
        lines.push(withRail(`    ${highlightMatch(item.hint, activeQuery, isActive ? warm : muted)}`));
      }
      return lines;
    };

    const renderSummary = () => {
      if (!multiple) {
        const filtered = filterItems();
        const current = filtered[cursor];
        if (!current) {
          return withBranch(muted('Current: (none)'));
        }
        return withBranch(`${warm('Current:')} ${strong(current.label)}`);
      }

      const summary = summarizeLabels(
        items.filter((item) => selected.has(item.value)).map((item) => item.label)
      );
      return withBranch(`${warm('Selected:')} ${summary}`);
    };

    const render = (mode = 'active') => {
      clear();

      const filtered = syncCursor();
      const lines = [];
      lines.push(`${HEADER_MARKER} ${strong(message)}`);

      if (mode === 'submit') {
        const submitted = multiple
          ? summarizeLabels(items.filter((item) => selected.has(item.value)).map((item) => item.label))
          : filtered[cursor]
            ? filtered[cursor].label
            : '';
        lines.push(withBranch(warm(submitted || '(none)')));
      } else if (mode === 'cancel') {
        lines.push(withBranch(danger('Cancelled')));
      } else {
        lines.push(withRail(renderInstructions()));
        if (searchable) {
          lines.push(withRail(`${muted('Filter:')} ${query ? warm(query) : muted('(none)')}`));
        }
        if (errorMessage) {
          lines.push(withRail(danger(errorMessage)));
        }
        lines.push(RAIL);

        if (!filtered.length) {
          lines.push(withRail(muted(emptyText)));
        } else {
          const visibleCount = Math.min(maxVisible, filtered.length);
          const start = Math.max(
            0,
            Math.min(cursor - Math.floor(visibleCount / 2), filtered.length - visibleCount)
          );
          const visible = filtered.slice(start, start + visibleCount);

          visible.forEach((item, index) => {
            const actualIndex = start + index;
            const isActive = actualIndex === cursor;
            const isSelected = multiple && selected.has(item.value);
            lines.push(renderRow(item, isActive, isSelected, query));

            const detailLines = renderDetails(item, isActive, query);
            if (detailLines.length && isActive) {
              lines.push(...detailLines);
            }
          });

          if (filtered.length > visibleCount) {
            lines.push(RAIL);
            lines.push(withRail(muted(`Showing ${start + 1}-${start + visible.length} of ${filtered.length}`)));
          }
        }

        lines.push(renderSummary());
      }

      process.stdout.write(`${lines.join('\n')}\n`);
      lastHeight = measureRenderedHeight(lines);
    };

    const cleanup = () => {
      process.stdin.removeListener('keypress', onKeypress);
      process.stdin.setRawMode(false);
      rl.close();
    };

    const submit = () => {
      const filtered = syncCursor();
      if (multiple) {
        if (required && selected.size === 0) {
          errorMessage = 'Select at least one option.';
          render();
          return;
        }

        render('submit');
        cleanup();
        resolve(items.filter((item) => selected.has(item.value)).map((item) => item.value));
        return;
      }

      if (required && !filtered[cursor]) {
        errorMessage = 'Select an option before continuing.';
        render();
        return;
      }

      render('submit');
      cleanup();
      resolve(filtered[cursor] ? filtered[cursor].value : cancelSymbol);
    };

    const cancel = () => {
      render('cancel');
      cleanup();
      resolve(cancelSymbol);
    };

    const onKeypress = (input, key = {}) => {
      const filtered = syncCursor();

      if (key.ctrl && key.name === 'c') {
        cancel();
        return;
      }

      if (key.name === 'return') {
        submit();
        return;
      }

      if (key.name === 'escape') {
        if (searchable && query) {
          query = '';
          errorMessage = '';
          render();
          return;
        }
        cancel();
        return;
      }

      if (key.name === 'up' || key.name === 'left') {
        errorMessage = '';
        cursor = Math.max(0, cursor - 1);
        render();
        return;
      }

      if (key.name === 'down' || key.name === 'right') {
        errorMessage = '';
        cursor = Math.min(Math.max(filtered.length - 1, 0), cursor + 1);
        render();
        return;
      }

      if (multiple && key.name === 'space') {
        const item = filtered[cursor];
        if (item) {
          if (selected.has(item.value)) {
            selected.delete(item.value);
          } else {
            selected.add(item.value);
          }
          errorMessage = '';
        }
        render();
        return;
      }

      if (multiple && input === 'a') {
        const allSelected = items.length > 0 && items.every((item) => selected.has(item.value));
        selected.clear();
        if (!allSelected) {
          items.forEach((item) => selected.add(item.value));
        }
        errorMessage = '';
        render();
        return;
      }

      if (searchable && key.name === 'backspace') {
        query = query.slice(0, -1);
        cursor = 0;
        errorMessage = '';
        render();
        return;
      }

      if (searchable && input && input.length === 1 && !key.ctrl && !key.meta) {
        query += input;
        cursor = 0;
        errorMessage = '';
        render();
      }
    };

    process.stdin.on('keypress', onKeypress);
    render();
  });
}

module.exports = {
  cancelSymbol,
  confirmPrompt,
  multiselectPrompt,
  searchMultiselect,
  selectPrompt,
};
