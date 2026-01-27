'use strict';

const React = require('react');
const { useState, useEffect } = React;
const { Box, Text } = require('ink');

const SPINNER_FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];

function Spinner() {
  const [frame, setFrame] = useState(0);
  
  useEffect(() => {
    const timer = setInterval(() => {
      setFrame((prev) => (prev + 1) % SPINNER_FRAMES.length);
    }, 80);
    return () => clearInterval(timer);
  }, []);
  
  return <Text color="#d95f2b">{SPINNER_FRAMES[frame]}</Text>;
}

function Installing({ skills, destination, status }) {
  const destLabel = destination === 'global' ? 'global (user-level)' : 'project';
  
  if (status.error) {
    return (
      <Box flexDirection="column">
        <Box>
          <Text color="red">✖ </Text>
          <Text color="red">Installation failed</Text>
        </Box>
        <Box marginLeft={2}>
          <Text dimColor>{status.error}</Text>
        </Box>
      </Box>
    );
  }
  
  if (status.done) {
    return (
      <Box flexDirection="column">
        <Box marginBottom={1}>
          <Text color="#d95f2b">✔ </Text>
          <Text color="#d95f2b" bold>Installation complete!</Text>
        </Box>
        
        {status.results.map((result, idx) => (
          <Box key={idx} marginLeft={2}>
            <Text color={result.skipped ? '#6c645c' : '#d95f2b'}>
              {result.skipped ? '○ ' : '● '}
            </Text>
            <Text color="white">{result.skill}</Text>
            <Text color="#6c645c"> - {result.path}</Text>
            {result.skipped ? <Text color="#6c645c"> (skipped)</Text> : null}
          </Box>
        ))}
        
        <Box marginTop={1}>
          <Text dimColor>Restart your editor to pick up new skills.</Text>
        </Box>
      </Box>
    );
  }
  
  return (
    <Box flexDirection="column">
      <Box>
        <Spinner />
        <Text color="white"> Installing {skills.length} skill(s) to </Text>
        <Text color="#d95f2b">{destLabel}</Text>
        <Text color="white">...</Text>
      </Box>
      
      <Box marginTop={1} flexDirection="column" marginLeft={2}>
        {skills.map((skill) => (
          <Box key={skill.name}>
            <Text color="#6c645c">• {skill.name}</Text>
          </Box>
        ))}
      </Box>
    </Box>
  );
}

module.exports = Installing;
