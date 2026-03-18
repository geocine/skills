'use strict';

const fs = require('fs');
const path = require('path');
const { isExplicitExternalSkillName } = require('./external-skills');

function findSkills(repoRoot) {
  const fromJson = loadSkillsJson(repoRoot);
  if (fromJson.length) {
    return fromJson;
  }

  const skillsRoot = path.join(repoRoot, 'skills');
  const base = dirExists(skillsRoot) ? skillsRoot : repoRoot;

  const entries = fs.readdirSync(base, { withFileTypes: true });
  const skills = entries
    .filter((entry) => entry.isDirectory() && fs.existsSync(path.join(base, entry.name, 'SKILL.md')))
    .filter((entry) => !isExplicitExternalSkillName(entry.name))
    .map((entry) => {
      const skillPath = path.join(base, entry.name);
      const skillFile = path.join(skillPath, 'SKILL.md');
      const metadata = readFrontmatter(skillFile);
      return {
        name: metadata.name || entry.name,
        path: skillPath,
        description: metadata.description || '',
        shortDescription:
          metadata.shortDescription ||
          metadata.shortDescriptionMeta ||
          buildShortDescription(metadata.description),
        repository: metadata.repository || 'any',
        author: metadata.author || '',
      };
    })
    .sort((a, b) => a.name.localeCompare(b.name));

  if (!skills.length) {
    throw new Error('No skills found in the skills repository.');
  }

  return skills;
}

function loadSkillsJson(repoRoot) {
  const skillsFile = path.join(repoRoot, 'skills.json');
  if (!fs.existsSync(skillsFile)) {
    return [];
  }

  try {
    const raw = fs.readFileSync(skillsFile, 'utf8');
    const data = JSON.parse(raw);
    if (!Array.isArray(data)) {
      return [];
    }

    return data
      .filter((skill) => skill && typeof skill.name === 'string')
      .map((skill) => ({
        name: skill.name,
        description: skill.description || '',
        shortDescription: skill.shortDescription || buildShortDescription(skill.description),
        repository: skill.repository || 'any',
        author: skill.author || '',
        path: skill.path
          ? path.join(repoRoot, skill.path)
          : path.join(repoRoot, 'skills', skill.name),
      }))
      .filter((skill) => !isExplicitExternalSkillName(skill.name))
      .filter((skill) => fs.existsSync(skill.path))
      .sort((a, b) => a.name.localeCompare(b.name));
  } catch {
    return [];
  }
}

function applyListFilter(skills, options = {}) {
  const query = String(options.filter || '')
    .trim()
    .toLowerCase();
  if (!query) {
    return skills;
  }

  return skills.filter((skill) =>
    [skill.name, skill.description, skill.shortDescription, skill.repository, skill.author]
      .filter(Boolean)
      .some((field) => String(field).toLowerCase().includes(query))
  );
}

function splitRepositoryField(repository) {
  const values = Array.isArray(repository) ? repository : String(repository || 'any').split(',');
  const seen = new Set();
  const result = [];

  values.forEach((value) => {
    const normalized = String(value || '').trim();
    if (!normalized) {
      return;
    }
    const key = normalized.toLowerCase();
    if (seen.has(key)) {
      return;
    }
    seen.add(key);
    result.push(normalized);
  });

  return result.length ? result : ['any'];
}

function filterSkillsByName(skills, names) {
  const nameSet = new Set((names || []).map((name) => String(name).toLowerCase()));
  const selected = skills.filter((skill) => nameSet.has(skill.name.toLowerCase()));
  if (!selected.length) {
    throw new Error(`No matching skills selected: ${(names || []).join(', ')}`);
  }
  return selected;
}

function buildShortDescription(description) {
  if (!description) {
    return '';
  }

  let base = String(description).replace(/\s+/g, ' ').trim();
  const cutTokens = [' Use when ', ' Use after ', ' Use for ', ' Use if ', ' Use to '];
  for (const token of cutTokens) {
    const index = base.indexOf(token);
    if (index > 0) {
      base = base.slice(0, index).trim();
      break;
    }
  }

  base = base.replace(/\s*\([^)]*\)\s*/g, ' ').replace(/\s+/g, ' ').trim();

  const trimTokens = [' including ', ' such as ', ' e.g. ', ' e.g., ', ' for example '];
  for (const token of trimTokens) {
    const index = base.toLowerCase().indexOf(token.trim());
    if (index > 0) {
      base = base.slice(0, index).trim();
      break;
    }
  }

  if (base.includes('. ')) {
    base = base.split('. ')[0].trim();
  }

  if (base.length > 90) {
    const commaCut = base.split(',')[0].trim();
    if (commaCut.length >= 40) {
      base = commaCut;
    }
  }

  if (base.length > 90) {
    const andCut = base.split(' and ')[0].trim();
    if (andCut.length >= 40) {
      base = andCut;
    }
  }

  if (base.length > 90) {
    base = `${base.slice(0, 87).trimEnd()}...`;
  }

  return base;
}

function readFrontmatter(filePath) {
  if (!fs.existsSync(filePath)) {
    return {};
  }

  const content = fs.readFileSync(filePath, 'utf8');
  const lines = content.split(/\r?\n/);
  if (!lines.length || lines[0].trim() !== '---') {
    return {};
  }

  const data = {};
  let currentSection = '';

  for (let index = 1; index < lines.length; index += 1) {
    const line = lines[index];
    if (line.trim() === '---') {
      break;
    }

    if (!line.trim()) {
      continue;
    }

    const indent = line.match(/^\s*/)[0].length;
    const separatorIndex = line.indexOf(':');
    if (separatorIndex === -1) {
      continue;
    }

    const rawKey = line.slice(0, separatorIndex).trim();
    const rawValue = line.slice(separatorIndex + 1).trim();

    if (!rawValue) {
      currentSection = indent === 0 ? rawKey : currentSection;
      continue;
    }

    const value = unquote(rawValue);
    if (indent > 0 && currentSection) {
      data[`${currentSection}.${rawKey}`] = value;
    } else {
      currentSection = '';
      data[rawKey] = value;
    }
  }

  return {
    name: data.name || '',
    description: data.description || '',
    repository: data.repository || '',
    author: data.author || '',
    shortDescription:
      data.shortDescription ||
      data['short-description'] ||
      '',
    shortDescriptionMeta:
      data['metadata.short-description'] ||
      data['metadata.shortDescription'] ||
      '',
  };
}

function unquote(value) {
  if (
    (value.startsWith('"') && value.endsWith('"')) ||
    (value.startsWith("'") && value.endsWith("'"))
  ) {
    return value.slice(1, -1);
  }
  return value;
}

function dirExists(targetPath) {
  try {
    return fs.statSync(targetPath).isDirectory();
  } catch {
    return false;
  }
}

module.exports = {
  applyListFilter,
  buildShortDescription,
  filterSkillsByName,
  findSkills,
  loadSkillsJson,
  readFrontmatter,
  splitRepositoryField,
};
