'use strict';

const React = require('react');
const { useState } = React;
const { Box, Text, useInput } = require('ink');

const EDITORS = [
  { key: 'cursor', name: 'Cursor', folder: '.cursor', localFolder: '.cursor' },
  { key: 'copilot', name: 'GitHub Copilot', folder: '.copilot', localFolder: '.github' },
  { key: 'opencode', name: 'OpenCode', folder: '.config/opencode', localFolder: '.opencode' },
  { key: 'claude', name: 'Claude Code', folder: '.claude', localFolder: '.claude' },
  { key: 'codex', name: 'Codex', folder: '.codex', localFolder: '.codex' },
];

function EditorSelect({ initialSelected, onSelect, onBack }) {
  const [cursor, setCursor] = useState(0);
  const [selected, setSelected] = useState(() => {
    // Initialize from previously selected editors
    if (initialSelected && initialSelected.length > 0) {
      return new Set(initialSelected.map(e => e.key));
    }
    return new Set();
  });

  useInput((input, key) => {
    // Back with 'b' or backspace
    if (input === 'b' || key.backspace) {
      if (onBack) onBack();
      return;
    }
    
    if (key.upArrow) {
      setCursor((prev) => (prev > 0 ? prev - 1 : EDITORS.length - 1));
    }
    if (key.downArrow) {
      setCursor((prev) => (prev < EDITORS.length - 1 ? prev + 1 : 0));
    }
    
    // Toggle with space or left/right arrows
    if (input === ' ' || key.leftArrow || key.rightArrow) {
      const editor = EDITORS[cursor];
      setSelected((prev) => {
        const next = new Set(prev);
        if (next.has(editor.key)) {
          next.delete(editor.key);
        } else {
          next.add(editor.key);
        }
        return next;
      });
    }
    
    // Select all / deselect all with 'a'
    if (input === 'a') {
      const allSelected = EDITORS.every((e) => selected.has(e.key));
      if (allSelected) {
        setSelected(new Set());
      } else {
        setSelected(new Set(EDITORS.map(e => e.key)));
      }
    }
    
    // Submit with enter
    if (key.return && selected.size > 0) {
      const selectedEditors = EDITORS.filter((e) => selected.has(e.key));
      onSelect(selectedEditors);
    }
  });

  return (
    <Box flexDirection="column">
      <Box marginBottom={1}>
        <Text bold color="white">Select editors </Text>
        <Text dimColor>({selected.size} selected)</Text>
      </Box>
      
      <Box flexDirection="column" borderStyle="single" borderColor="gray" paddingX={1}>
        {EDITORS.map((editor, idx) => {
          const isCursor = idx === cursor;
          const isSelected = selected.has(editor.key);
          
          return (
            <Box key={editor.key}>
              <Text color={isSelected ? '#d95f2b' : 'gray'}>
                {isSelected ? '◉ ' : '○ '}
              </Text>
              <Text color={isCursor ? '#d95f2b' : 'gray'}>
                {isCursor ? '❯ ' : '  '}
              </Text>
              <Text bold={isCursor} color={isCursor ? 'white' : 'gray'}>
                {editor.name}
              </Text>
              <Text color="#f6d3c4"> ({editor.localFolder}/skills)</Text>
            </Box>
          );
        })}
      </Box>
      
      <Box marginTop={1}>
        <Text>
          <Text color="#f6d3c4">↑↓</Text>
          <Text color="#6c645c"> nav</Text>
          <Text color="#6c645c"> • </Text>
          <Text color="#f6d3c4">space</Text>
          <Text color="#6c645c"> toggle</Text>
          <Text color="#6c645c"> • </Text>
          <Text color="#f6d3c4">a</Text>
          <Text color="#6c645c"> all</Text>
          <Text color="#6c645c"> • </Text>
          <Text color="#f6d3c4">b</Text>
          <Text color="#6c645c"> back</Text>
          <Text color="#6c645c"> • </Text>
          <Text color="#d95f2b">enter</Text>
          <Text color="#6c645c"> confirm</Text>
        </Text>
      </Box>
    </Box>
  );
}

module.exports = EditorSelect;
module.exports.EDITORS = EDITORS;
