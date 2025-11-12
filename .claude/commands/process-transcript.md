# Process Video Transcript

You are working within the PBS Wisconsin Editorial Assistant CLI workflow.

Your task is to process a video transcript through Phase 1 (Brainstorming) using the video-metadata-seo-editor agent.

## Context

The user has started a project and provided a transcript. You need to:

1. Read the transcript from the project directory
2. Invoke the video-metadata-seo-editor agent with the transcript
3. Save the brainstorming output to the project directory using the template format
4. Update the project state to mark Phase 1 as complete
5. Display a success message with next steps

## Agent Instructions

When you invoke the video-metadata-seo-editor agent, provide:
- The full transcript content
- Instructions to create a brainstorming document (Phase 1)
- Request that output follow the template format in `templates/brainstorming_standard.md`

## Output

After the agent completes:
1. Save output to `{project_dir}/01_brainstorming.md`
2. Update `.state.json` to mark Phase 1 complete
3. Display celebration message with progress update
4. Suggest next steps (Phase 2: provide draft copy for revision)
