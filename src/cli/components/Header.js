'use strict';

const React = require('react');
const { Box, Text } = require('ink');

function Header() {
  return (
    <Box>
      <Text color="#d95f2b">●</Text>
      <Text> </Text>
      <Text bold color="white">GEOCINE SKILLS</Text>
      <Text dimColor> installer</Text>
    </Box>
  );
}

module.exports = Header;
