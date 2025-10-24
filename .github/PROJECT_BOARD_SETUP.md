# GitHub Project Board Setup

This document describes how to integrate the SoundHash repository with GitHub Projects for tracking the roadmap.

## Project: @onnwee's soundhash

The user has created a GitHub Project called **"@onnwee's soundhash"** to visualize and track the roadmap progress.

### Accessing the Project

- **Project URL**: <https://github.com/users/onnwee/projects>
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

The repository includes GitHub Actions workflows to automate project board management:

#### Automated Features (via `.github/workflows/project-automation.yml`)

1. **Auto-add items**: When an issue or PR is created or reopened, automatically add it to the project

**Note**: For automatic status updates (moving items to "Done", "In Review", etc.), use GitHub's built-in project automation workflows rather than custom GitHub Actions. This is more reliable and doesn't require complex GraphQL queries.

#### Setup Requirements

To enable automation, configure the following:

1. **Create Personal Access Token (PAT)**
   - Go to GitHub Settings → Developer settings → Personal access tokens → Fine-grained tokens
   - Create token with:
     - Resource owner: Your user account
     - Repository access: Only select repositories → soundhash
     - Permissions: 
       - Repository permissions: Issues (Read and write), Pull requests (Read and write)
       - Organization permissions: Projects (Read and write)
   - Copy the token

2. **Add Token to Repository**
   - Go to repository Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `PROJECT_TOKEN`
   - Value: Paste your PAT
   - Click "Add secret"

3. **Update Project URL in Workflow**
   - Find your project number:
     - Visit <https://github.com/users/onnwee/projects>
     - Click on "@onnwee's soundhash"
     - Note the number in the URL (e.g., `/projects/5` means project number is 5)
   - Edit `.github/workflows/project-automation.yml`
   - Update the `project-url` line with your actual project number

4. **Test the Automation**
   - Create a test issue to verify it's automatically added to the project

#### Manual Automation (Recommended for Status Updates)

For automatic status updates when items are closed or PRs are merged, use GitHub's built-in project automation:

1. Open your project at <https://github.com/users/onnwee/projects>
2. Click "..." menu → "Workflows"
3. Enable these built-in workflows:
   - "Auto-add to project" - adds new items automatically (alternative to GitHub Actions)
   - "Item closed" - moves closed items to Done
   - "Pull request merged" - updates status when PRs merge

**Recommendation**: Use GitHub Actions for adding items (more reliable) and built-in workflows for status updates (simpler to configure).

#### Automation Status

- ✅ GitHub Actions workflow created (`.github/workflows/project-automation.yml`)
- ✅ Auto-add functionality implemented
- ⚠️ Requires `PROJECT_TOKEN` secret configuration
- ⚠️ Requires project URL verification
- ℹ️ Status updates: Use GitHub's built-in project workflows (simpler and more reliable)

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

1. Navigate to <https://github.com/users/onnwee/projects>
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
