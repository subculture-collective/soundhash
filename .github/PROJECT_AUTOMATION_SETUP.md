# GitHub Project Board Automation - Quick Start Guide

This guide will help you set up automated project board management for the SoundHash repository.

## Overview

The repository includes GitHub Actions automation to:
- ✅ Automatically add new issues and PRs to the project board

For automatic status updates (moving items between columns when closed, merged, etc.):
- ✅ Use GitHub's built-in project workflows (recommended - simpler and more reliable)
- See "Alternative: Built-in GitHub Automation" section below

## Prerequisites

1. A GitHub Project (beta/v2) already exists at `https://github.com/users/onnwee/projects`
2. Repository access to configure secrets
3. A GitHub Personal Access Token (PAT)

## Setup Steps

### Step 1: Create Personal Access Token

1. Go to GitHub Settings → Developer settings → Personal access tokens → [Fine-grained tokens](https://github.com/settings/tokens?type=beta)
2. Click "Generate new token"
3. Configure the token:
   - **Token name**: `soundhash-project-automation`
   - **Resource owner**: Your user account (onnwee)
   - **Repository access**: Only select repositories → `subculture-collective/soundhash`
   - **Permissions**:
     - Repository permissions:
       - Issues: Read and write
       - Pull requests: Read and write
     - Account permissions:
       - Projects: Read and write
   - **Expiration**: Set as appropriate (recommend 90 days or 1 year)
4. Click "Generate token"
5. **IMPORTANT**: Copy the token immediately (it won't be shown again)

### Step 2: Add Token to Repository

1. Go to [repository settings](https://github.com/subculture-collective/soundhash/settings/secrets/actions)
2. Click "New repository secret"
3. Configure the secret:
   - **Name**: `PROJECT_TOKEN` (must be exactly this)
   - **Value**: Paste the PAT from Step 1
4. Click "Add secret"

### Step 3: Find Your Project Number

1. Visit https://github.com/users/onnwee/projects
2. Click on "@onnwee's soundhash" project
3. Look at the URL in your browser: `https://github.com/users/onnwee/projects/NUMBER`
4. Note the project NUMBER (e.g., if URL shows `/projects/5`, the number is `5`)

### Step 4: Update Workflow Configuration

1. Open `.github/workflows/project-automation.yml` in the repository
2. Find the line: `project-url: https://github.com/users/onnwee/projects/1`
3. Update the number `1` with your actual project number from Step 3
4. Commit the change

### Step 5: Configure Project Board Columns

Make sure your project has the following status field with these options:
- **Todo** (default for new items)
- **In Progress**
- **In Review**
- **Done**

To configure in GitHub Projects:
1. Open your project
2. Click on the "Status" field header → "Edit values"
3. Add/rename options to match the above

### Step 6: Test the Automation

1. Create a test issue in the repository
2. Check that it appears on the project board within a few seconds

### Step 7: Enable Status Update Automation (Recommended)

For automatic status updates when items are closed or PRs are merged:

1. Open your project at https://github.com/users/onnwee/projects
2. Click the "..." menu (top right)
3. Select "Workflows"
4. Enable these built-in workflows:
   - ✅ "Item closed" - moves items to Done when closed
   - ✅ "Pull request merged" - updates status when PRs merge

**Why use built-in workflows for status updates?**
- Simpler to configure (no GraphQL queries needed)
- More reliable (maintained by GitHub)
- No additional token permissions required
- Works immediately without code changes

## Alternative: Built-in GitHub Automation for Everything

If you prefer to use GitHub's built-in project automation for both adding and updating items:

1. Open your project at https://github.com/users/onnwee/projects
2. Click the "..." menu (top right)
3. Select "Workflows"
4. Enable all relevant workflows:
   - ✅ "Auto-add to project" - automatically adds new items
   - ✅ "Item closed" - moves items to Done when closed
   - ✅ "Pull request merged" - updates status when PRs merge

**Note**: Built-in workflows may have limitations compared to custom GitHub Actions, but are simpler for basic use cases.

## Bulk-Adding Existing Issues

To add all existing issues to the project board:

### Method A: Using Project UI
1. Open your project
2. Click "+" button
3. Select "Add items from repository"
4. Choose `subculture-collective/soundhash`
5. Select all issues or filter as needed
6. Click "Add selected items"

### Method B: Using GitHub CLI
```bash
# First, find your project number
gh project list --owner @me

# Then bulk-add issues (replace PROJECT_NUMBER)
for i in $(seq 1 34); do
  gh project item-add PROJECT_NUMBER \
    --owner @me \
    --url https://github.com/subculture-collective/soundhash/issues/${i}
done
```

## Configuring Project Views

Create the following views in your project for better organization:

### View 1: Kanban Board (Default)
- **Group by**: Status
- **Columns**: Todo, In Progress, In Review, Done
- **Filter**: Show open items

### View 2: By Milestone
- **Group by**: Milestone
- **Show**: M0, M1, M2, M3, M4
- **Filter**: Show open items

### View 3: By Priority
- **Group by**: Labels
- **Show**: priority:P0, priority:P1, priority:P2
- **Sort**: Priority descending

### View 4: By Area
- **Group by**: Labels
- **Show**: area:* labels (core, ingestion, db, api, etc.)

## Troubleshooting

### Issue: Items not being added automatically
- Verify `PROJECT_TOKEN` secret is set correctly
- Check workflow runs at: https://github.com/subculture-collective/soundhash/actions
- Ensure project URL in workflow matches your actual project

### Issue: Workflow fails with authentication error
- Regenerate PAT with correct permissions
- Update `PROJECT_TOKEN` secret
- Verify token hasn't expired

### Issue: Items added but status not updating
- Check that project has "Status" field configured
- Verify status options match expected values (Todo, In Progress, In Review, Done)
- May need custom GraphQL queries for complex status updates

## Related Documentation

- [PROJECT_BOARD_SETUP.md](PROJECT_BOARD_SETUP.md) - Detailed project board configuration
- [PROJECT_INTEGRATION_SUMMARY.md](PROJECT_INTEGRATION_SUMMARY.md) - Implementation summary
- [GitHub Projects Documentation](https://docs.github.com/en/issues/planning-and-tracking-with-projects)
- [actions/add-to-project](https://github.com/actions/add-to-project) - Official action used

## Support

If you encounter issues:
1. Check [GitHub Actions logs](https://github.com/subculture-collective/soundhash/actions)
2. Review [GitHub Projects documentation](https://docs.github.com/en/issues/planning-and-tracking-with-projects)
3. Open an issue in the repository

---

Last updated: 2025-10-24
