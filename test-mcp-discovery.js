// Quick test to verify MCP server can discover the test project

import * as path from 'path';
import * as fs from 'fs/promises';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const OUTPUT_DIR = path.join(__dirname, 'OUTPUT');

async function scanProjectDirectory(projectPath) {
  try {
    const manifestPath = path.join(projectPath, 'manifest.json');
    const projectName = path.basename(projectPath);

    let manifest = null;
    try {
      const manifestContent = await fs.readFile(manifestPath, 'utf-8');
      manifest = JSON.parse(manifestContent);
    } catch {
      console.log('No manifest found');
    }

    const files = await fs.readdir(projectPath);
    const hasBrainstorming = files.some(f =>
      f === 'brainstorming.md' || f === 'digital_shorts_report.md'
    );

    return {
      name: projectName,
      program: manifest?.program_type || 'Unknown',
      processed_date: manifest?.processing_started?.split('T')[0] || 'Unknown',
      has_brainstorming: hasBrainstorming,
      status: manifest?.status || 'unknown',
      transcript_summary: manifest?.content_summary,
      duration: manifest?.metadata?.duration
    };
  } catch (error) {
    console.error(`Error scanning ${projectPath}:`, error);
    return null;
  }
}

async function listProcessedProjects() {
  try {
    const entries = await fs.readdir(OUTPUT_DIR, { withFileTypes: true });
    const projects = [];

    for (const entry of entries) {
      if (entry.isDirectory()) {
        const projectPath = path.join(OUTPUT_DIR, entry.name);
        const project = await scanProjectDirectory(projectPath);
        if (project) {
          projects.push(project);
        }
      }
    }

    return projects.sort((a, b) =>
      (b.processed_date || '').localeCompare(a.processed_date || '')
    );
  } catch (error) {
    console.error('Error listing projects:', error);
    return [];
  }
}

// Run the test
console.log('Testing MCP server discovery functionality...\n');
const projects = await listProcessedProjects();

console.log(`Found ${projects.length} project(s):\n`);
projects.forEach((project, i) => {
  console.log(`${i + 1}. ${project.name} (${project.program})`);
  console.log(`   Status: ${project.status}`);
  console.log(`   Processed: ${project.processed_date}`);
  console.log(`   Duration: ${project.duration || 'unknown'}`);
  console.log(`   Has brainstorming: ${project.has_brainstorming}`);
  if (project.transcript_summary) {
    console.log(`   Summary: ${project.transcript_summary.substring(0, 100)}...`);
  }
  console.log('');
});

console.log('✅ MCP discovery test complete!');
