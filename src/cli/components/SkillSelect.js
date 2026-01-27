'use strict';

const React = require('react');
const { useState, useMemo } = React;
const { Box, Text, useInput } = require('ink');

// Highlights matching text with yellow color
function HighlightText({ text, query, baseColor }) {
  if (!query || !text) {
    return <Text color={baseColor}>{text}</Text>;
  }
  
  const lowerText = text.toLowerCase();
  const lowerQuery = query.toLowerCase();
  const parts = [];
  let lastIndex = 0;
  let index = lowerText.indexOf(lowerQuery);
  let key = 0;
  
  while (index !== -1) {
    // Add text before match
    if (index > lastIndex) {
      parts.push(
        <Text key={key++} color={baseColor}>{text.slice(lastIndex, index)}</Text>
      );
    }
    // Add highlighted match (orange accent)
    parts.push(
      <Text key={key++} color="#d95f2b" bold>{text.slice(index, index + query.length)}</Text>
    );
    lastIndex = index + query.length;
    index = lowerText.indexOf(lowerQuery, lastIndex);
  }
  
  // Add remaining text
  if (lastIndex < text.length) {
    parts.push(
      <Text key={key++} color={baseColor}>{text.slice(lastIndex)}</Text>
    );
  }
  
  return <>{parts}</>;
}

function SkillSelect({ skills, initialSelected, onSelect, showDetails }) {
  const [filter, setFilter] = useState('');
  const [filterMode, setFilterMode] = useState(false);
  const [showDescriptions, setShowDescriptions] = useState(false);
  const [cursor, setCursor] = useState(0);
  const [selected, setSelected] = useState(() => {
    // Initialize from previously selected skills
    if (initialSelected && initialSelected.length > 0) {
      return new Set(initialSelected.map(s => s.name));
    }
    return new Set();
  });

  const filteredSkills = useMemo(() => {
    if (!filter) return skills;
    const query = filter.toLowerCase();
    return skills.filter((skill) =>
      skill.name.toLowerCase().includes(query) ||
      (skill.shortDescription || '').toLowerCase().includes(query) ||
      (skill.repository || '').toLowerCase().includes(query)
    );
  }, [skills, filter]);

  // Reset cursor when filter changes
  React.useEffect(() => {
    setCursor(0);
  }, [filter]);

  useInput((input, key) => {
    // Navigation
    if (key.upArrow) {
      if (filterMode) {
        // In filter mode, up arrow navigates list
        setCursor((prev) => Math.max(0, prev - 1));
      } else if (cursor === 0) {
        // At first item, go to filter mode
        setFilterMode(true);
      } else {
        setCursor((prev) => prev - 1);
      }
      return;
    }
    if (key.downArrow) {
      if (filterMode) {
        // Exit filter mode and go to list
        setFilterMode(false);
        if (filteredSkills.length === 0) {
          setFilter('');
        }
      } else {
        setCursor((prev) => Math.min(filteredSkills.length - 1, prev + 1));
      }
      return;
    }
    
    // Escape exits filter mode and clears filter if no matches
    if (key.escape) {
      if (filterMode) {
        setFilterMode(false);
        // Clear filter if no matches
        if (filteredSkills.length === 0) {
          setFilter('');
        }
      } else if (filter) {
        setFilter('');
      }
      return;
    }
    
    // Toggle filter mode with '/'
    if (input === '/') {
      if (filterMode) {
        // Exiting filter mode - clear filter if no matches
        setFilterMode(false);
        if (filteredSkills.length === 0) {
          setFilter('');
        }
      } else {
        setFilterMode(true);
      }
      return;
    }
    
    // Filter mode: typing goes to filter
    if (filterMode) {
      if (key.backspace || key.delete) {
        setFilter((prev) => prev.slice(0, -1));
      } else if (input && input.length === 1 && !key.ctrl && !key.meta) {
        if (/[a-zA-Z0-9\-_ ]/.test(input)) {
          setFilter((prev) => prev + input);
        }
      }
      return;
    }
    
    // Toggle selection with space or left/right arrows
    if ((input === ' ' || key.leftArrow || key.rightArrow) && filteredSkills.length > 0) {
      const skill = filteredSkills[cursor];
      setSelected((prev) => {
        const next = new Set(prev);
        if (next.has(skill.name)) {
          next.delete(skill.name);
        } else {
          next.add(skill.name);
        }
        return next;
      });
    }
    
    // Select all / deselect all with 'a'
    if (input === 'a') {
      const allNames = filteredSkills.map((s) => s.name);
      const allSelected = allNames.every((name) => selected.has(name));
      if (allSelected) {
        setSelected((prev) => {
          const next = new Set(prev);
          allNames.forEach((name) => next.delete(name));
          return next;
        });
      } else {
        setSelected((prev) => {
          const next = new Set(prev);
          allNames.forEach((name) => next.add(name));
          return next;
        });
      }
      return;
    }
    
    // Toggle descriptions with 'd'
    if (input === 'd') {
      setShowDescriptions((prev) => !prev);
      return;
    }
    
    // Submit with enter
    if (key.return) {
      const selectedSkills = skills.filter((s) => selected.has(s.name));
      onSelect(selectedSkills);
    }
  });

  const visibleCount = Math.min(8, filteredSkills.length);
  const startIdx = Math.max(0, Math.min(cursor - Math.floor(visibleCount / 2), filteredSkills.length - visibleCount));
  const visibleSkills = filteredSkills.slice(startIdx, startIdx + visibleCount);

  return (
    <Box flexDirection="column">
      <Box marginBottom={1}>
        <Text bold color="white">Select skills </Text>
        <Text dimColor>({selected.size} selected)</Text>
      </Box>
      
      {/* Filter input */}
      <Box marginBottom={1}>
        <Text color={filterMode ? '#d95f2b' : 'gray'}>
          {filterMode ? '>' : '/'} Filter: 
        </Text>
        <Text color="white">{filter}</Text>
        {filterMode ? <Text color="#d95f2b">▌</Text> : null}
        {filter ? (
          <Text dimColor> ({filteredSkills.length} matches)</Text>
        ) : null}
      </Box>
      
      {/* Skills list */}
      <Box flexDirection="column" borderStyle="single" borderColor="gray" paddingX={1}>
        {visibleSkills.length === 0 ? (
          <Text dimColor italic>No skills match "{filter}"</Text>
        ) : (
          visibleSkills.map((skill, idx) => {
            const actualIdx = startIdx + idx;
            const isCursor = actualIdx === cursor;
            const isSelected = selected.has(skill.name);
            const repo = skill.repository && skill.repository !== 'any' ? skill.repository : '';
            
            return (
              <Box key={skill.name} flexDirection="column">
                <Box>
                  <Text color={isSelected ? '#d95f2b' : 'gray'}>
                    {isSelected ? '◉ ' : '○ '}
                  </Text>
                  <Text color={isCursor ? '#d95f2b' : 'gray'}>
                    {isCursor ? '❯ ' : '  '}
                  </Text>
                  <HighlightText 
                    text={skill.name} 
                    query={filter} 
                    baseColor={isCursor ? 'white' : 'gray'} 
                  />
                  {repo ? (
                    <>
                      <Text color="#f6d3c4"> [</Text>
                      <HighlightText text={repo} query={filter} baseColor="#f6d3c4" />
                      <Text color="#f6d3c4">]</Text>
                    </>
                  ) : null}
                </Box>
                {(isCursor || filterMode || showDescriptions) && skill.shortDescription ? (
                  <Box marginLeft={6}>
                    <HighlightText 
                      text={showDetails ? skill.description : skill.shortDescription} 
                      query={filter} 
                      baseColor="#6c645c" 
                    />
                  </Box>
                ) : null}
              </Box>
            );
          })
        )}
      </Box>
      
      {/* Scroll indicator */}
      {filteredSkills.length > visibleCount ? (
        <Box marginTop={0}>
          <Text dimColor>
            {startIdx + 1}-{Math.min(startIdx + visibleCount, filteredSkills.length)} of {filteredSkills.length}
          </Text>
        </Box>
      ) : null}
      
      <Box marginTop={1}>
        {filterMode ? (
          <Text>
            <Text color="#6c645c">type to filter</Text>
            <Text color="#6c645c"> • </Text>
            <Text color="#f6d3c4">esc</Text>
            <Text color="#6c645c"> exit</Text>
            <Text color="#6c645c"> • </Text>
            <Text color="#f6d3c4">↓</Text>
            <Text color="#6c645c"> to list</Text>
          </Text>
        ) : (
          <Text>
            <Text color="#f6d3c4">↑↓</Text>
            <Text color="#6c645c"> nav</Text>
            <Text color="#6c645c"> • </Text>
            <Text color="#f6d3c4">/</Text>
            <Text color="#6c645c"> filter</Text>
            <Text color="#6c645c"> • </Text>
            <Text color="#f6d3c4">space</Text>
            <Text color="#6c645c"> toggle</Text>
            <Text color="#6c645c"> • </Text>
            <Text color="#f6d3c4">a</Text>
            <Text color="#6c645c"> all</Text>
            <Text color="#6c645c"> • </Text>
            <Text color="#f6d3c4">d</Text>
            <Text color="#6c645c"> desc</Text>
            <Text color="#6c645c"> • </Text>
            <Text color="#d95f2b">enter</Text>
            <Text color="#6c645c"> confirm</Text>
          </Text>
        )}
      </Box>
    </Box>
  );
}

module.exports = SkillSelect;
