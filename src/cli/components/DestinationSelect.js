'use strict';

const React = require('react');
const { useState, useMemo } = React;
const { Box, Text, useInput } = require('ink');

function DestinationSelect({ editors, onSelect, onBack }) {
  const [selected, setSelected] = useState(0);
  
  const options = useMemo(() => {
    const globalPaths = editors.map(e => `~/${e.folder}/skills`).join(', ');
    const localPaths = editors.map(e => `./${e.localFolder || e.folder}/skills`).join(', ');
    
    return [
      { 
        key: 'global', 
        label: 'Global (user-level)', 
        desc: globalPaths,
        icon: '◈'
      },
      { 
        key: 'project', 
        label: 'Project (local)', 
        desc: localPaths,
        icon: '▣'
      },
    ];
  }, [editors]);

  useInput((input, key) => {
    // Back with 'b' or backspace
    if (input === 'b' || key.backspace) {
      if (onBack) onBack();
      return;
    }
    
    if (key.upArrow || input === 'k') {
      setSelected((prev) => (prev > 0 ? prev - 1 : options.length - 1));
    }
    if (key.downArrow || input === 'j') {
      setSelected((prev) => (prev < options.length - 1 ? prev + 1 : 0));
    }
    // Select with enter, space, or left/right arrows
    if (key.return || input === ' ' || key.leftArrow || key.rightArrow) {
      onSelect(options[selected].key);
    }
  });

  return (
    <Box flexDirection="column">
      <Box marginBottom={1}>
        <Text bold color="white">Where to install?</Text>
      </Box>
      
      {options.map((opt, idx) => (
        <Box key={opt.key} flexDirection="column" marginBottom={idx === selected ? 1 : 0}>
          <Box>
            <Text color={idx === selected ? '#d95f2b' : 'gray'}>
              {idx === selected ? '❯ ' : '  '}
            </Text>
            <Text color={idx === selected ? '#d95f2b' : 'gray'}>{opt.icon}</Text>
            <Text> </Text>
            <Text bold={idx === selected} color={idx === selected ? 'white' : 'gray'}>
              {opt.label}
            </Text>
          </Box>
          {idx === selected ? (
            <Box marginLeft={6}>
              <Text color="#f6d3c4">{opt.desc}</Text>
            </Box>
          ) : null}
        </Box>
      ))}
      
      <Box marginTop={1}>
        <Text>
          <Text color="#f6d3c4">↑↓</Text>
          <Text color="#6c645c"> nav</Text>
          <Text color="#6c645c"> • </Text>
          <Text color="#f6d3c4">b</Text>
          <Text color="#6c645c"> back</Text>
          <Text color="#6c645c"> • </Text>
          <Text color="#d95f2b">enter</Text>
          <Text color="#6c645c"> select</Text>
        </Text>
      </Box>
    </Box>
  );
}

module.exports = DestinationSelect;
