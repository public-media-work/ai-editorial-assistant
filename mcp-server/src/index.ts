#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";
import * as path from "path";
import * as fs from "fs/promises";
import { spawn } from "child_process";
import { fileURLToPath } from "url";

// Get project root (editorial-assistant directory)
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, "../..");
const OUTPUT_DIR = path.join(PROJECT_ROOT, "OUTPUT");
const TRANSCRIPTS_DIR = path.join(PROJECT_ROOT, "transcripts");
const QUEUE_FILE = path.join(PROJECT_ROOT, ".processing-requests.json");
const MAX_PREVIEW_HEAD_BYTES = 4000;
const MAX_PREVIEW_TAIL_BYTES = 1500;

// Types
interface ProjectManifest {
  transcript_file: string;
  project_name: string;
  program_type: string;
  processing_started: string;
  processing_completed?: string;
  status: string;
  content_summary?: string;
  deliverables: {
    brainstorming?: { file: string; created: string; agent: string };
    formatted_transcript?: { file: string; created: string; agent: string };
    timestamps?: { file: string; created: string; agent: string };
    copy_revisions?: Array<{ file: string; version: number; created: string }>;
    seo_data?: { file: string; created: string } | null;
  };
  editing_sessions?: Array<any>;
  metadata?: {
    duration?: string;
    speakers?: string[];
    topics?: string[];
  };
}

interface ProcessedProject {
  name: string;
  program: string;
  processed_date: string;
  has_brainstorming: boolean;
  has_formatted_transcript: boolean;
  has_timestamps: boolean;
  has_revisions: boolean;
  status: string;
  transcript_summary?: string;
  manifest_path: string;
}

// Utility functions
function isPathAllowed(targetPath: string) {
  const resolved = path.resolve(targetPath);
  const allowedRoots = [OUTPUT_DIR, TRANSCRIPTS_DIR];
  return allowedRoots.some(root => resolved === root || resolved.startsWith(root + path.sep));
}

function dedupe(names: Array<string | null | undefined>): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const name of names) {
    if (!name) continue;
    if (!seen.has(name)) {
      seen.add(name);
      out.push(name);
    }
  }
  return out;
}

async function findExistingFile(projectPath: string, candidates: Array<string | null | undefined>): Promise<string | null> {
  for (const candidate of dedupe(candidates)) {
    try {
      await fs.access(path.join(projectPath, candidate));
      return candidate;
    } catch {
      continue;
    }
  }
  return null;
}

async function getFilePreview(filePath: string) {
  const resolved = path.resolve(filePath);
  const stats = await fs.stat(resolved);

  const fileHandle = await fs.open(resolved, "r");
  try {
    const headBytes = Math.min(MAX_PREVIEW_HEAD_BYTES, stats.size);
    const headBuffer = Buffer.alloc(headBytes);
    await fileHandle.read(headBuffer, 0, headBytes, 0);
    let preview = headBuffer.toString("utf-8");

    if (stats.size > MAX_PREVIEW_HEAD_BYTES) {
      const tailBytes = Math.min(MAX_PREVIEW_TAIL_BYTES, stats.size - MAX_PREVIEW_HEAD_BYTES);
      const tailBuffer = Buffer.alloc(tailBytes);
      await fileHandle.read(tailBuffer, 0, tailBytes, stats.size - tailBytes);
      preview = `${preview}\n...\n${tailBuffer.toString("utf-8")}`;
    }

    return {
      path: resolved,
      size: stats.size,
      modified: stats.mtime.toISOString(),
      preview
    };
  } finally {
    await fileHandle.close();
  }
}

async function listProjectFiles(projectName: string) {
  const projectPath = path.join(OUTPUT_DIR, projectName);
  const entries = await fs.readdir(projectPath, { withFileTypes: true });
  const files = [];

  for (const entry of entries) {
    if (entry.isFile()) {
      const fullPath = path.join(projectPath, entry.name);
      const stats = await fs.stat(fullPath);
      files.push({
        name: entry.name,
        path: fullPath,
        size: stats.size,
        modified: stats.mtime.toISOString()
      });
    }
  }

  return files.sort((a, b) => b.modified.localeCompare(a.modified));
}

async function readProjectFile(targetPath: string, maxBytes?: number) {
  const resolved = path.resolve(PROJECT_ROOT, targetPath);
  if (!isPathAllowed(resolved)) {
    throw new Error("Access to this path is not allowed");
  }

  const content = await fs.readFile(resolved, "utf-8");
  if (typeof maxBytes === "number" && maxBytes > 0 && content.length > maxBytes) {
    const truncated = content.slice(0, maxBytes);
    const omitted = content.length - maxBytes;
    return `${truncated}\n...[truncated ${omitted} chars]`;
  }
  return content;
}

async function scanProjectDirectory(projectPath: string): Promise<ProcessedProject | null> {
  try {
    const manifestPath = path.join(projectPath, "manifest.json");
    const projectName = path.basename(projectPath);

    let manifest: ProjectManifest | null = null;

    // Try to read manifest if exists
    try {
      const manifestContent = await fs.readFile(manifestPath, "utf-8");
      manifest = JSON.parse(manifestContent);
    } catch {
      // No manifest, scan directory manually
    }

    // Resolve deliverable filenames (prefer manifest entries, fallback to common names)
    const brainstormingFile = await findExistingFile(projectPath, [
      manifest?.deliverables?.brainstorming?.file,
      "brainstorming.md",
      `${projectName}_brainstorming.md`,
      "digital_shorts_report.md",
      `${projectName}_digital_shorts_report.md`
    ]);

    const formattedFile = await findExistingFile(projectPath, [
      manifest?.deliverables?.formatted_transcript?.file,
      "formatted_transcript.md",
      `${projectName}_formatted_transcript.md`
    ]);

    const timestampFile = await findExistingFile(projectPath, [
      manifest?.deliverables?.timestamps?.file,
      "timestamp_report.md",
      `${projectName}_timestamp_report.md`
    ]);

    // Scan files in directory for revisions/metadata
    const files = await fs.readdir(projectPath);
    const hasRevisions = files.some(f => f.includes("copy_revision"));

    // Determine status
    let status = "unknown";
    if (manifest?.status) {
      status = manifest.status;
    } else if (brainstormingFile && formattedFile) {
      status = "ready_for_editing";
    } else if (brainstormingFile) {
      status = "processing";
    }

    return {
      name: projectName,
      program: manifest?.program_type || "Unknown",
      processed_date: manifest?.processing_started?.split("T")[0] || "Unknown",
      has_brainstorming: Boolean(brainstormingFile),
      has_formatted_transcript: Boolean(formattedFile),
      has_timestamps: Boolean(timestampFile),
      has_revisions: hasRevisions,
      status,
      transcript_summary: manifest?.content_summary,
      manifest_path: manifestPath
    };
  } catch (error) {
    console.error(`Error scanning ${projectPath}:`, error);
    return null;
  }
}

async function listProcessedProjects(): Promise<ProcessedProject[]> {
  try {
    const entries = await fs.readdir(OUTPUT_DIR, { withFileTypes: true });
    const projects: ProcessedProject[] = [];

    for (const entry of entries) {
      if (entry.isDirectory()) {
        const projectPath = path.join(OUTPUT_DIR, entry.name);
        const project = await scanProjectDirectory(projectPath);
        if (project) {
          projects.push(project);
        }
      }
    }

    // Sort by processed date, most recent first
    return projects.sort((a, b) =>
      (b.processed_date || "").localeCompare(a.processed_date || "")
    );
  } catch (error) {
    console.error("Error listing projects:", error);
    return [];
  }
}

async function loadProjectForEditing(projectName: string): Promise<any> {
  const projectPath = path.join(OUTPUT_DIR, projectName);

  try {
    // Load manifest
    let manifest: ProjectManifest | null = null;
    try {
      const manifestContent = await fs.readFile(
        path.join(projectPath, "manifest.json"),
        "utf-8"
      );
      manifest = JSON.parse(manifestContent);
    } catch {
      // No manifest
    }

    // Build lightweight previews (avoid full loads)
    let transcriptPreview = null;
    if (manifest?.transcript_file) {
      try {
        transcriptPreview = await getFilePreview(path.join(TRANSCRIPTS_DIR, manifest.transcript_file));
      } catch {
        transcriptPreview = null;
      }
    }

    const brainstormingFile = await findExistingFile(projectPath, [
      manifest?.deliverables?.brainstorming?.file,
      "brainstorming.md",
      `${projectName}_brainstorming.md`,
      "digital_shorts_report.md",
      `${projectName}_digital_shorts_report.md`
    ]);

    let brainstormingPreview = null;
    if (brainstormingFile) {
      try {
        brainstormingPreview = await getFilePreview(path.join(projectPath, brainstormingFile));
      } catch {
        brainstormingPreview = null;
      }
    }

    const formattedFile = await findExistingFile(projectPath, [
      manifest?.deliverables?.formatted_transcript?.file,
      "formatted_transcript.md",
      `${projectName}_formatted_transcript.md`
    ]);

    let formattedPreview = null;
    if (formattedFile) {
      try {
        formattedPreview = await getFilePreview(path.join(projectPath, formattedFile));
      } catch {
        formattedPreview = null;
      }
    }

    // Load most recent revision preview if exists
    let latestRevisionPreview = null;
    try {
      const files = await fs.readdir(projectPath);
      const revisionFiles = files
        .filter(f => f.includes("copy_revision"))
        .sort()
        .reverse();

      if (revisionFiles.length > 0) {
        latestRevisionPreview = await getFilePreview(path.join(projectPath, revisionFiles[0]));
      }
    } catch {
      // No revisions
    }

    let files: Array<{ name: string; path: string; size: number; modified: string }> = [];
    try {
      files = await listProjectFiles(projectName);
    } catch {
      files = [];
    }

    return {
      project_name: projectName,
      manifest,
      transcript: transcriptPreview
        ? {
            file: manifest?.transcript_file || "unknown",
            duration: manifest?.metadata?.duration || "unknown",
            ...transcriptPreview
          }
        : null,
      brainstorming: brainstormingPreview,
      formatted_transcript: formattedPreview,
      latest_revision: latestRevisionPreview,
      program_rules: manifest?.program_type || "Unknown",
      files
    };
  } catch (error) {
    throw new Error(`Failed to load project ${projectName}: ${error}`);
  }
}

async function saveRevision(
  projectName: string,
  content: string,
  version?: number
): Promise<string> {
  const projectPath = path.join(OUTPUT_DIR, projectName);

  // Determine version number
  let versionNum = version;
  if (!versionNum) {
    try {
      const files = await fs.readdir(projectPath);
      const revisionFiles = files.filter(f => f.startsWith("copy_revision"));
      versionNum = revisionFiles.length + 1;
    } catch {
      versionNum = 1;
    }
  }

  const filename = `copy_revision_v${versionNum}.md`;
  const filePath = path.join(projectPath, filename);

  await fs.writeFile(filePath, content, "utf-8");

  // Update manifest if exists
  try {
    const manifestPath = path.join(projectPath, "manifest.json");
    const manifestContent = await fs.readFile(manifestPath, "utf-8");
    const manifest: ProjectManifest = JSON.parse(manifestContent);

    if (!manifest.deliverables.copy_revisions) {
      manifest.deliverables.copy_revisions = [];
    }

    manifest.deliverables.copy_revisions.push({
      file: filename,
      version: versionNum,
      created: new Date().toISOString()
    });

    if (!manifest.editing_sessions) {
      manifest.editing_sessions = [];
    }

    manifest.editing_sessions.push({
      timestamp: new Date().toISOString(),
      action: "revision_saved",
      version: versionNum
    });

    await fs.writeFile(manifestPath, JSON.stringify(manifest, null, 2), "utf-8");
  } catch {
    // Manifest doesn't exist or couldn't be updated
  }

  return filePath;
}

async function getQueueStatus() {
  try {
    const content = await fs.readFile(QUEUE_FILE, "utf-8");
    return JSON.parse(content);
  } catch {
    return [];
  }
}

async function runQueueProcessing() {
  return new Promise<string>((resolve, reject) => {
    const proc = spawn("python3", ["scripts/process_queue_auto.py"], {
      cwd: PROJECT_ROOT
    });

    let output = "";
    const append = (chunk: Buffer) => {
      output += chunk.toString();
      // keep only last ~8000 chars to prevent token bloat
      const maxLen = 8000;
      if (output.length > maxLen) {
        output = output.slice(-maxLen);
      }
    };

    proc.stdout.on("data", append);
    proc.stderr.on("data", append);
    proc.on("error", (err) => reject(err));
    proc.on("close", (code) => {
      resolve(output.trim() || `Queue processor exited with code ${code}`);
    });
  });
}

interface QueueItem {
  project: string;
  transcript_file: string;
  queued_at: string;
  status: string;
  needs_brainstorming: boolean;
  needs_formatting: boolean;
  transcript_length_chars: number;
  estimated_processing_minutes: number;
  started_at?: string;
  error?: string | null;
  completed_at?: string;
  priority?: number;
}

async function archiveUnprocessedTranscripts(): Promise<{
  archived: string[];
  skipped: string[];
  errors: string[];
}> {
  const archiveDir = path.join(TRANSCRIPTS_DIR, "archive");
  const archived: string[] = [];
  const skipped: string[] = [];
  const errors: string[] = [];

  // Ensure archive directory exists
  try {
    await fs.mkdir(archiveDir, { recursive: true });
  } catch {
    // Directory likely exists
  }

  // Get all transcript files (excluding archive directory and hidden files)
  const entries = await fs.readdir(TRANSCRIPTS_DIR, { withFileTypes: true });
  const transcriptFiles = entries.filter(
    (e) => e.isFile() && e.name.endsWith(".txt") && !e.name.startsWith(".")
  );

  for (const file of transcriptFiles) {
    const sourcePath = path.join(TRANSCRIPTS_DIR, file.name);
    const destPath = path.join(archiveDir, file.name);

    try {
      // Check if file already exists in archive
      try {
        await fs.access(destPath);
        skipped.push(`${file.name} (already exists in archive)`);
        continue;
      } catch {
        // File doesn't exist in archive, proceed with move
      }

      await fs.rename(sourcePath, destPath);
      archived.push(file.name);
    } catch (err) {
      errors.push(`${file.name}: ${err instanceof Error ? err.message : String(err)}`);
    }
  }

  return { archived, skipped, errors };
}

async function prioritizeTranscript(transcriptFile: string): Promise<{
  success: boolean;
  message: string;
  newPosition?: number;
}> {
  // Load current queue
  let queue: QueueItem[] = [];
  try {
    const content = await fs.readFile(QUEUE_FILE, "utf-8");
    queue = JSON.parse(content);
  } catch {
    return { success: false, message: "Could not read processing queue" };
  }

  // Find the transcript in the queue
  const index = queue.findIndex(
    (item) =>
      item.transcript_file === transcriptFile ||
      item.project === transcriptFile ||
      item.transcript_file.includes(transcriptFile) ||
      item.project.includes(transcriptFile)
  );

  if (index === -1) {
    // List available pending items for helpful error
    const pendingItems = queue
      .filter((item) => item.status === "pending" || item.status === "failed")
      .map((item) => item.project);
    return {
      success: false,
      message: `Transcript "${transcriptFile}" not found in queue. Available items: ${pendingItems.join(", ") || "none"}`
    };
  }

  const item = queue[index];

  // Check if already at front or completed
  if (item.status === "completed") {
    return { success: false, message: `Transcript "${item.project}" is already completed` };
  }

  if (item.status === "processing") {
    return { success: false, message: `Transcript "${item.project}" is currently being processed` };
  }

  // Find first pending/failed item position
  const firstPendingIndex = queue.findIndex(
    (q) => q.status === "pending" || q.status === "failed"
  );

  if (index === firstPendingIndex) {
    return { success: true, message: `Transcript "${item.project}" is already at the front of the queue`, newPosition: 1 };
  }

  // Remove item from current position and insert at front of pending items
  queue.splice(index, 1);
  queue.splice(firstPendingIndex, 0, item);

  // Update queued_at to now to indicate prioritization
  item.queued_at = new Date().toISOString();

  // Save updated queue
  try {
    await fs.writeFile(QUEUE_FILE, JSON.stringify(queue, null, 2), "utf-8");
  } catch (err) {
    return { success: false, message: `Failed to save queue: ${err instanceof Error ? err.message : String(err)}` };
  }

  return {
    success: true,
    message: `Transcript "${item.project}" moved to front of queue`,
    newPosition: firstPendingIndex + 1
  };
}

async function archiveOldOutputFolders(maxAgeDays: number = 30): Promise<{
  archived: Array<{ name: string; age_days: number; completed_date: string }>;
  skipped: Array<{ name: string; reason: string }>;
  errors: string[];
}> {
  const archiveDir = path.join(OUTPUT_DIR, "archive");
  const archived: Array<{ name: string; age_days: number; completed_date: string }> = [];
  const skipped: Array<{ name: string; reason: string }> = [];
  const errors: string[] = [];

  const now = new Date();
  const maxAgeMs = maxAgeDays * 24 * 60 * 60 * 1000;

  // Ensure archive directory exists
  try {
    await fs.mkdir(archiveDir, { recursive: true });
  } catch {
    // Directory likely exists
  }

  // Get all project directories (excluding archive and hidden)
  const entries = await fs.readdir(OUTPUT_DIR, { withFileTypes: true });
  const projectDirs = entries.filter(
    (e) => e.isDirectory() && e.name !== "archive" && !e.name.startsWith(".")
  );

  for (const dir of projectDirs) {
    const projectPath = path.join(OUTPUT_DIR, dir.name);
    const manifestPath = path.join(projectPath, "manifest.json");
    const destPath = path.join(archiveDir, dir.name);

    try {
      // Check if already exists in archive
      try {
        await fs.access(destPath);
        skipped.push({ name: dir.name, reason: "already exists in archive" });
        continue;
      } catch {
        // Doesn't exist in archive, proceed
      }

      // Try to read manifest for completion date
      let completedDate: Date | null = null;
      let completedDateStr = "";

      try {
        const manifestContent = await fs.readFile(manifestPath, "utf-8");
        const manifest: ProjectManifest = JSON.parse(manifestContent);

        if (manifest.processing_completed) {
          completedDate = new Date(manifest.processing_completed);
          completedDateStr = manifest.processing_completed;
        } else if (manifest.processing_started) {
          // Fall back to started date if no completion date
          completedDate = new Date(manifest.processing_started);
          completedDateStr = manifest.processing_started;
        }
      } catch {
        // No manifest or invalid - skip this folder
        skipped.push({ name: dir.name, reason: "no manifest.json found" });
        continue;
      }

      if (!completedDate) {
        skipped.push({ name: dir.name, reason: "no processing date in manifest" });
        continue;
      }

      // Check age
      const ageMs = now.getTime() - completedDate.getTime();
      const ageDays = Math.floor(ageMs / (24 * 60 * 60 * 1000));

      if (ageMs < maxAgeMs) {
        skipped.push({ name: dir.name, reason: `only ${ageDays} days old (threshold: ${maxAgeDays})` });
        continue;
      }

      // Move to archive
      await fs.rename(projectPath, destPath);
      archived.push({
        name: dir.name,
        age_days: ageDays,
        completed_date: completedDateStr.split("T")[0]
      });

    } catch (err) {
      errors.push(`${dir.name}: ${err instanceof Error ? err.message : String(err)}`);
    }
  }

  return { archived, skipped, errors };
}

const DOCS_ARCHIVE_DIR = path.join(PROJECT_ROOT, "docs", "archive");

// Patterns that indicate development/coordination docs (case-insensitive)
const DEV_DOC_PATTERNS = [
  /^(DEV|WIP|DRAFT|TODO|TEMP)_/i,           // Explicit dev prefixes
  /_COMPLETE\.md$/i,                         // Milestone completion markers
  /_SETUP\.md$/i,                            // Setup docs
  /_SPEC\.md$/i,                             // Specifications (once implemented)
  /_PLAN\.md$/i,                             // Planning docs
  /_STATUS\.md$/i,                           // Status updates
  /_TEST\.md$/i,                             // Test documentation
  /^READY_/i,                                // Ready-to markers
  /WORKFLOW/i,                               // Workflow docs
  /COORDINATION/i,                           // Agent coordination
  /ARCHITECTURE/i,                           // Architecture docs
  /CODE_REVIEW/i,                            // Code review notes
];

// Files to always keep in root (never archive)
const PROTECTED_DOCS = [
  "README.md",
  "CLAUDE.md",
  "CHANGELOG.md",
  "CONTRIBUTING.md",
  "LICENSE.md",
  "HOW_TO_USE.md",
  "QUICK_REFERENCE.md",
];

interface DevDocInfo {
  name: string;
  path: string;
  modified: string;
  age_days: number;
  matched_pattern?: string;
  protected: boolean;
}

async function auditDevDocs(maxAgeDays: number = 14): Promise<{
  candidates: DevDocInfo[];
  protected: DevDocInfo[];
  total_root_docs: number;
}> {
  const candidates: DevDocInfo[] = [];
  const protectedDocs: DevDocInfo[] = [];
  const now = new Date();

  // Get all .md files in project root
  const entries = await fs.readdir(PROJECT_ROOT, { withFileTypes: true });
  const mdFiles = entries.filter(
    (e) => e.isFile() && e.name.endsWith(".md")
  );

  for (const file of mdFiles) {
    const filePath = path.join(PROJECT_ROOT, file.name);
    const stats = await fs.stat(filePath);
    const ageMs = now.getTime() - stats.mtime.getTime();
    const ageDays = Math.floor(ageMs / (24 * 60 * 60 * 1000));

    const docInfo: DevDocInfo = {
      name: file.name,
      path: filePath,
      modified: stats.mtime.toISOString().split("T")[0],
      age_days: ageDays,
      protected: PROTECTED_DOCS.includes(file.name),
    };

    if (docInfo.protected) {
      protectedDocs.push(docInfo);
      continue;
    }

    // Check if matches dev doc patterns
    for (const pattern of DEV_DOC_PATTERNS) {
      if (pattern.test(file.name)) {
        docInfo.matched_pattern = pattern.toString();
        break;
      }
    }

    // Consider for archival if: matches pattern OR older than maxAgeDays
    if (docInfo.matched_pattern || ageDays > maxAgeDays) {
      candidates.push(docInfo);
    }
  }

  return {
    candidates: candidates.sort((a, b) => b.age_days - a.age_days),
    protected: protectedDocs,
    total_root_docs: mdFiles.length,
  };
}

async function archiveDevDocs(fileNames: string[]): Promise<{
  archived: string[];
  skipped: string[];
  errors: string[];
}> {
  const archived: string[] = [];
  const skipped: string[] = [];
  const errors: string[] = [];

  // Ensure archive directory exists
  try {
    await fs.mkdir(DOCS_ARCHIVE_DIR, { recursive: true });
  } catch {
    // Directory likely exists
  }

  for (const fileName of fileNames) {
    // Safety check: don't archive protected files
    if (PROTECTED_DOCS.includes(fileName)) {
      skipped.push(`${fileName} (protected)`);
      continue;
    }

    const sourcePath = path.join(PROJECT_ROOT, fileName);
    const destPath = path.join(DOCS_ARCHIVE_DIR, fileName);

    try {
      // Check source exists
      try {
        await fs.access(sourcePath);
      } catch {
        skipped.push(`${fileName} (not found)`);
        continue;
      }

      // Check if already in archive
      try {
        await fs.access(destPath);
        skipped.push(`${fileName} (already in archive)`);
        continue;
      } catch {
        // Good, doesn't exist in archive
      }

      await fs.rename(sourcePath, destPath);
      archived.push(fileName);
    } catch (err) {
      errors.push(`${fileName}: ${err instanceof Error ? err.message : String(err)}`);
    }
  }

  return { archived, skipped, errors };
}

// Define tools
const tools: Tool[] = [
  {
    name: "list_processed_projects",
    description: "List all processed video projects with their current status. Shows which projects are ready for editing.",
    inputSchema: {
      type: "object",
      properties: {},
      required: []
    }
  },
  {
    name: "load_project_for_editing",
    description: "Load lightweight context for a project: manifest, file pointers, sizes, and short previews. Use read_project_file to fetch full content when needed.",
    inputSchema: {
      type: "object",
      properties: {
        project_name: {
          type: "string",
          description: "Name of the project (e.g., '9UNP2005HD', '2WLI1206HD')"
        }
      },
      required: ["project_name"]
    }
  },
  {
    name: "save_revision",
    description: "Save a copy revision document back to the project directory. Auto-increments version numbers.",
    inputSchema: {
      type: "object",
      properties: {
        project_name: {
          type: "string",
          description: "Name of the project"
        },
        content: {
          type: "string",
          description: "Markdown content of the revision document"
        },
        version: {
          type: "number",
          description: "Optional version number. If not provided, auto-increments."
        }
      },
      required: ["project_name", "content"]
    }
  },
  {
    name: "get_project_summary",
    description: "Get a quick summary of a specific project's status and available deliverables.",
    inputSchema: {
      type: "object",
      properties: {
        project_name: {
          type: "string",
          description: "Name of the project"
        }
      },
      required: ["project_name"]
    }
  },
  {
    name: "get_formatted_transcript",
    description: "Load the formatted transcript for fact-checking during copy editing. Use this to verify quotes, speaker names, and content accuracy.",
    inputSchema: {
      type: "object",
      properties: {
        project_name: {
          type: "string",
          description: "Name of the project"
        }
      },
      required: ["project_name"]
    }
  },
  {
    name: "list_project_files",
    description: "List files for a project with sizes and modified dates (no content).",
    inputSchema: {
      type: "object",
      properties: {
        project_name: {
          type: "string",
          description: "Name of the project"
        }
      },
      required: ["project_name"]
    }
  },
  {
    name: "read_project_file",
    description: "Read a specific project or transcript file on demand. Supports optional truncation via max_bytes.",
    inputSchema: {
      type: "object",
      properties: {
        file_path: {
          type: "string",
          description: "Absolute or project-relative path under OUTPUT/ or transcripts/"
        },
        max_bytes: {
          type: "number",
          description: "Optional max bytes to return; content will be truncated if larger."
        }
      },
      required: ["file_path"]
    }
  },
  {
    name: "get_queue_status",
    description: "Read the processing queue (.processing-requests.json) with statuses.",
    inputSchema: {
      type: "object",
      properties: {},
      required: []
    }
  },
  {
    name: "run_queue_processing",
    description: "Trigger the Python queue processor and return recent log output.",
    inputSchema: {
      type: "object",
      properties: {},
      required: []
    }
  },
  {
    name: "archive_unprocessed_transcripts",
    description: "Move all unprocessed transcript files from /transcripts/ to /transcripts/archive/. Use this to clean up the transcripts directory after processing is complete.",
    inputSchema: {
      type: "object",
      properties: {},
      required: []
    }
  },
  {
    name: "prioritize_transcript",
    description: "Move a specific transcript to the front of the processing queue. The transcript must already be in the queue with status 'pending' or 'failed'.",
    inputSchema: {
      type: "object",
      properties: {
        transcript: {
          type: "string",
          description: "Project name or transcript filename to prioritize (e.g., '9UNP2005HD' or '9UNP2005HD_ForClaude.txt')"
        }
      },
      required: ["transcript"]
    }
  },
  {
    name: "archive_old_output_folders",
    description: "Move output project folders older than a specified number of days to OUTPUT/archive/. Age is determined by the processing_completed date in manifest.json.",
    inputSchema: {
      type: "object",
      properties: {
        max_age_days: {
          type: "number",
          description: "Maximum age in days before archiving (default: 30)"
        }
      },
      required: []
    }
  },
  {
    name: "audit_dev_docs",
    description: "Audit markdown files in the project root for potential cleanup. Identifies development notes, coordination files, and stale documentation that could be archived. Returns candidates for archival without making changes.",
    inputSchema: {
      type: "object",
      properties: {
        max_age_days: {
          type: "number",
          description: "Consider non-pattern-matched docs older than this for archival (default: 14)"
        }
      },
      required: []
    }
  },
  {
    name: "archive_dev_docs",
    description: "Move specified development documentation files to docs/archive/. Use audit_dev_docs first to identify candidates. Protected files (README.md, CLAUDE.md, etc.) cannot be archived.",
    inputSchema: {
      type: "object",
      properties: {
        files: {
          type: "array",
          items: { type: "string" },
          description: "Array of filenames to archive (e.g., ['DEV_NOTES.md', 'OLD_SPEC.md'])"
        }
      },
      required: ["files"]
    }
  }
];

// Create server
const server = new Server(
  {
    name: "editorial-assistant-mcp",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
      resources: {},
    },
  }
);

// Handle list tools request
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return { tools };
});

// Handle resource listing
server.setRequestHandler(ListResourcesRequestSchema, async () => {
  const projects = await listProcessedProjects();

  const resources = projects.map((project) => ({
    uri: `editorial-assistant://project/${project.name}`,
    name: `${project.name} - ${project.program || 'Unknown'}`,
    description: project.transcript_summary || `Status: ${project.status}`,
    mimeType: "application/json"
  }));

  return { resources };
});

// Handle resource reading
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const uri = request.params.uri;

  // Parse URI: editorial-assistant://project/{project_name}
  const match = uri.match(/^editorial-assistant:\/\/project\/(.+)$/);
  if (!match) {
    throw new Error(`Invalid resource URI: ${uri}`);
  }

  const projectName = match[1];
  const projectData = await loadProjectForEditing(projectName);

  return {
    contents: [{
      uri,
      mimeType: "application/json",
      text: JSON.stringify(projectData, null, 2)
    }]
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    if (name === "list_processed_projects") {
      const projects = await listProcessedProjects();
      return {
        content: [{
          type: "text",
          text: JSON.stringify(projects, null, 2)
        }]
      };
    }

    if (name === "load_project_for_editing") {
      if (!args || typeof args.project_name !== "string") {
        throw new Error("project_name parameter is required");
      }
      const projectData = await loadProjectForEditing(args.project_name);
      return {
        content: [{
          type: "text",
          text: JSON.stringify(projectData, null, 2)
        }]
      };
    }

    if (name === "save_revision") {
      if (!args || typeof args.project_name !== "string" || typeof args.content !== "string") {
        throw new Error("project_name and content parameters are required");
      }
      const filePath = await saveRevision(
        args.project_name,
        args.content,
        typeof args.version === "number" ? args.version : undefined
      );
      return {
        content: [{
          type: "text",
          text: `Revision saved to: ${filePath}`
        }]
      };
    }

    if (name === "get_project_summary") {
      if (!args || typeof args.project_name !== "string") {
        throw new Error("project_name parameter is required");
      }
      const projectPath = path.join(OUTPUT_DIR, args.project_name);
      const project = await scanProjectDirectory(projectPath);
      return {
        content: [{
          type: "text",
          text: JSON.stringify(project, null, 2)
        }]
      };
    }

    if (name === "get_formatted_transcript") {
      if (!args || typeof args.project_name !== "string") {
        throw new Error("project_name parameter is required");
      }
      const projectPath = path.join(OUTPUT_DIR, args.project_name);
      let manifest: ProjectManifest | null = null;
      try {
        const manifestContent = await fs.readFile(path.join(projectPath, "manifest.json"), "utf-8");
        manifest = JSON.parse(manifestContent);
      } catch {
        manifest = null;
      }

      const formattedFile = await findExistingFile(projectPath, [
        manifest?.deliverables?.formatted_transcript?.file,
        "formatted_transcript.md",
        `${args.project_name}_formatted_transcript.md`
      ]);

      try {
        if (!formattedFile) {
          throw new Error("formatted transcript missing");
        }
        const formattedTranscript = await fs.readFile(path.join(projectPath, formattedFile), "utf-8");
        return {
          content: [{
            type: "text",
            text: formattedTranscript
          }]
        };
      } catch (error) {
        return {
          content: [{
            type: "text",
            text: "Formatted transcript not yet generated for this project. Run the formatter agent first."
          }]
        };
      }
    }

    if (name === "list_project_files") {
      if (!args || typeof args.project_name !== "string") {
        throw new Error("project_name parameter is required");
      }
      const files = await listProjectFiles(args.project_name);
      return {
        content: [{
          type: "text",
          text: JSON.stringify(files, null, 2)
        }]
      };
    }

    if (name === "read_project_file") {
      if (!args || typeof args.file_path !== "string") {
        throw new Error("file_path parameter is required");
      }
      const content = await readProjectFile(
        args.file_path,
        typeof args.max_bytes === "number" ? args.max_bytes : undefined
      );
      return {
        content: [{
          type: "text",
          text: content
        }]
      };
    }

    if (name === "get_queue_status") {
      const queue = await getQueueStatus();
      return {
        content: [{
          type: "text",
          text: JSON.stringify(queue, null, 2)
        }]
      };
    }

    if (name === "run_queue_processing") {
      const output = await runQueueProcessing();
      return {
        content: [{
          type: "text",
          text: output
        }]
      };
    }

    if (name === "archive_unprocessed_transcripts") {
      const result = await archiveUnprocessedTranscripts();
      const summary = {
        archived_count: result.archived.length,
        skipped_count: result.skipped.length,
        error_count: result.errors.length,
        archived: result.archived,
        skipped: result.skipped,
        errors: result.errors
      };
      return {
        content: [{
          type: "text",
          text: JSON.stringify(summary, null, 2)
        }]
      };
    }

    if (name === "prioritize_transcript") {
      if (!args || typeof args.transcript !== "string") {
        throw new Error("transcript parameter is required");
      }
      const result = await prioritizeTranscript(args.transcript);
      return {
        content: [{
          type: "text",
          text: JSON.stringify(result, null, 2)
        }]
      };
    }

    if (name === "archive_old_output_folders") {
      const maxAgeDays = typeof args?.max_age_days === "number" ? args.max_age_days : 30;
      const result = await archiveOldOutputFolders(maxAgeDays);
      const summary = {
        archived_count: result.archived.length,
        skipped_count: result.skipped.length,
        error_count: result.errors.length,
        max_age_days: maxAgeDays,
        archived: result.archived,
        skipped: result.skipped,
        errors: result.errors
      };
      return {
        content: [{
          type: "text",
          text: JSON.stringify(summary, null, 2)
        }]
      };
    }

    if (name === "audit_dev_docs") {
      const maxAgeDays = typeof args?.max_age_days === "number" ? args.max_age_days : 14;
      const result = await auditDevDocs(maxAgeDays);
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            summary: `Found ${result.candidates.length} candidates for archival out of ${result.total_root_docs} total docs`,
            max_age_days: maxAgeDays,
            archive_candidates: result.candidates,
            protected_files: result.protected.map(d => d.name),
          }, null, 2)
        }]
      };
    }

    if (name === "archive_dev_docs") {
      if (!args || !Array.isArray(args.files)) {
        throw new Error("files parameter is required (array of filenames)");
      }
      const result = await archiveDevDocs(args.files as string[]);
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            archived_count: result.archived.length,
            skipped_count: result.skipped.length,
            error_count: result.errors.length,
            archived: result.archived,
            skipped: result.skipped,
            errors: result.errors,
            archive_location: "docs/archive/"
          }, null, 2)
        }]
      };
    }

    throw new Error(`Unknown tool: ${name}`);
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    return {
      content: [{
        type: "text",
        text: `Error: ${errorMessage}`
      }],
      isError: true
    };
  }
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Editorial Assistant MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
