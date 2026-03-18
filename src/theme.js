'use strict';

const pc = require('picocolors');

function colorDepth() {
  if (!pc.isColorSupported) {
    return 1;
  }

  if (process.stdout && typeof process.stdout.getColorDepth === 'function') {
    try {
      return process.stdout.getColorDepth();
    } catch {
      return 4;
    }
  }

  return 4;
}

function applyAnsi(text, open, close) {
  return pc.isColorSupported ? `${open}${text}${close}` : text;
}

function colorize(text, rgb, ansi256, fallback) {
  const value = String(text);
  const depth = colorDepth();

  if (depth >= 24) {
    return applyAnsi(value, `\x1b[38;2;${rgb[0]};${rgb[1]};${rgb[2]}m`, '\x1b[39m');
  }

  if (depth >= 8) {
    return applyAnsi(value, `\x1b[38;5;${ansi256}m`, '\x1b[39m');
  }

  return fallback(value);
}

function accent(text) {
  return colorize(text, [217, 95, 43], 166, pc.yellow);
}

function warm(text) {
  return colorize(text, [246, 211, 196], 224, pc.yellowBright);
}

function muted(text) {
  return colorize(text, [108, 100, 92], 241, (value) => pc.dim(value));
}

function strong(text) {
  return pc.bold(pc.white(String(text)));
}

function success(text) {
  return accent(text);
}

function danger(text) {
  return pc.red(String(text));
}

function info(text) {
  return muted(text);
}

function highlightMatch(text, query, baseColor = (value) => value) {
  const value = String(text || '');
  const needle = String(query || '').trim().toLowerCase();

  if (!needle) {
    return baseColor(value);
  }

  const lower = value.toLowerCase();
  const parts = [];
  let start = 0;
  let matchIndex = lower.indexOf(needle);

  while (matchIndex !== -1) {
    if (matchIndex > start) {
      parts.push(baseColor(value.slice(start, matchIndex)));
    }

    parts.push(accent(pc.bold(value.slice(matchIndex, matchIndex + needle.length))));
    start = matchIndex + needle.length;
    matchIndex = lower.indexOf(needle, start);
  }

  if (start < value.length) {
    parts.push(baseColor(value.slice(start)));
  }

  return parts.join('');
}

module.exports = {
  accent,
  danger,
  highlightMatch,
  info,
  muted,
  strong,
  success,
  warm,
};
