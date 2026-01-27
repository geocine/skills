'use strict';

const React = require('react');
const { useState } = React;
const { Box, Text, useApp, useInput } = require('ink');
const Header = require('./components/Header');
const SkillSelect = require('./components/SkillSelect');
const EditorSelect = require('./components/EditorSelect');
const DestinationSelect = require('./components/DestinationSelect');
const Installing = require('./components/Installing');

const SCREENS = {
  SKILLS: 'skills',
  EDITORS: 'editors',
  DESTINATION: 'destination',
  INSTALLING: 'installing',
};

function App({ skills, onInstall, options }) {
  const { exit } = useApp();
  const [screen, setScreen] = useState(SCREENS.SKILLS);
  const [selectedSkills, setSelectedSkills] = useState([]);
  const [selectedEditors, setSelectedEditors] = useState([]);
  const [destination, setDestination] = useState('global');
  const [installStatus, setInstallStatus] = useState({ done: false, results: [] });

  useInput((input, key) => {
    if (input === 'q' || (key.ctrl && input === 'c')) {
      exit();
    }
  });

  const handleSkillsSelect = (selected) => {
    if (selected.length === 0) {
      return;
    }
    setSelectedSkills(selected);
    setScreen(SCREENS.EDITORS);
  };

  const handleEditorsBack = () => {
    setScreen(SCREENS.SKILLS);
  };

  const handleEditorsSelect = (editors) => {
    setSelectedEditors(editors);
    setScreen(SCREENS.DESTINATION);
  };

  const handleDestinationBack = () => {
    setScreen(SCREENS.EDITORS);
  };

  const handleDestinationSelect = async (dest) => {
    setDestination(dest);
    setScreen(SCREENS.INSTALLING);
    
    try {
      const results = await onInstall(selectedSkills, selectedEditors, dest, options.force);
      setInstallStatus({ done: true, results });
      setTimeout(() => exit(), 1500);
    } catch (err) {
      setInstallStatus({ done: true, error: err.message, results: [] });
    }
  };

  return (
    <Box flexDirection="column" padding={1}>
      <Header />
      
      <Box marginTop={1}>
        {screen === SCREENS.SKILLS && (
          <SkillSelect 
            skills={skills} 
            initialSelected={selectedSkills}
            onSelect={handleSkillsSelect}
            showDetails={options.details}
          />
        )}
        
        {screen === SCREENS.EDITORS && (
          <EditorSelect 
            initialSelected={selectedEditors}
            onSelect={handleEditorsSelect} 
            onBack={handleEditorsBack}
          />
        )}
        
        {screen === SCREENS.DESTINATION && (
          <DestinationSelect 
            editors={selectedEditors} 
            onSelect={handleDestinationSelect}
            onBack={handleDestinationBack}
          />
        )}
        
        {screen === SCREENS.INSTALLING && (
          <Installing 
            skills={selectedSkills} 
            destination={destination}
            status={installStatus}
          />
        )}
      </Box>
      
      <Box marginTop={1}>
        <Text dimColor>Press q to quit</Text>
      </Box>
    </Box>
  );
}

module.exports = App;
