# GitHub Project Board Setup

This document describes how to integrate the SoundHash repository with GitHub Projects for tracking the roadmap.

## Project: @onnwee's soundhash

The user has created a GitHub Project called **"@onnwee's soundhash"** to visualize and track the roadmap progress.

### Accessing the Project

- **Project URL**: https://github.com/users/onnwee/projects
- **Alternative**: Navigate to your GitHub profile → Projects tab

### Connecting Issues to the Project

All issues in this repository (#1-#34) should be added to the project board. This can be done:

1. **Manually**: Open each issue and use the "Projects" sidebar to add it to "@onnwee's soundhash"
2. **Bulk**: Use GitHub's project automation to auto-add new issues
3. **Via API**: Use GitHub's GraphQL API to bulk-add existing issues

### Project Views

The project should include the following views:

1. **Kanban Board** (Default)
   - Columns: Todo, In Progress, In Review, Done
   - Group by: Status

2. **By Milestone**
   - Group by: Milestone (M0, M1, M2, M3)
   - Filter: Show open issues only

3. **By Priority**
   - Group by: Priority label (P0, P1, P2)
   - Sort: Priority descending

4. **By Area**
   - Group by: Area label (core, ingestion, db, api, bots, ops)
   - Filter: Show all

### Automation Rules

Configure the following automation:

1. **Auto-add items**: When an issue is created, automatically add it to the project
2. **Auto-archive**: When an issue is closed, move it to "Done"
3. **Auto-progress**: When a PR is linked, move issue to "In Progress"

### Master Roadmap Issue

Issue #34 serves as the master tracking issue. Keep it updated with:
- Links to all sub-issues
- Status checkboxes for each milestone deliverable
- Notes on scope changes or reprioritization

### Workflow

1. **Planning**: Create issues from the roadmap templates
2. **Assignment**: Assign issues to team members via the project board
3. **Tracking**: Update issue status by moving cards between columns
4. **Review**: Check off items in issue #34 as they're completed
5. **Reporting**: Use project insights to track velocity and burndown

### Labels and Milestones

The repository uses a structured label taxonomy:

- **Priority**: `priority:P0`, `priority:P1`, `priority:P2`
- **Type**: `type:ci`, `type:docs`, `type:security`, `type:performance`, etc.
- **Area**: `area:core`, `area:ingestion`, `area:db`, `area:api`, etc.
- **Standard**: `enhancement`, `bug`, `documentation`, `good first issue`, `help wanted`

Milestones:
- **M0**: Repo hygiene and CI (Baseline quality)
- **M1**: Core pipeline ready (Download → Segment → Fingerprint → Store)
- **M2**: Integrations, DX, and robustness
- **M3**: Release readiness and cadence

### Next Steps

1. Navigate to https://github.com/users/onnwee/projects
2. Open the "@onnwee's soundhash" project
3. Configure automation settings
4. Bulk-add all existing issues (#1-#34)
5. Set up the custom views described above
6. Start tracking work!

## Related Files

- `.github/ROADMAP_MASTER_ISSUE_BODY.md` - Template for the master issue
- `.github/labels.md` - Label taxonomy reference
- `.github/milestones.md` - Milestone definitions
- `ROADMAP.md` - Quick reference pointing to live tracking resources
