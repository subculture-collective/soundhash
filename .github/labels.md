# Label Taxonomy

This document defines the standard labels used across the SoundHash repository for consistent issue and PR triage.

## Type Labels (type:*)

Categorizes the kind of work or issue:

- `type:bug` - Something isn't working correctly
- `type:feature` - New feature or enhancement request
- `type:chore` - Maintenance, refactoring, or infrastructure work
- `type:docs` - Documentation improvements
- `type:test` - Testing-related changes
- `type:perf` - Performance improvements
- `type:security` - Security-related issues or improvements

## Area Labels (area:*)

Identifies the part of the codebase affected:

- `area:ingestion` - Channel and video ingestion
- `area:video-io` - Video download and processing (yt-dlp, ffmpeg)
- `area:fingerprinting` - Audio fingerprint extraction
- `area:matching` - Fingerprint matching and comparison
- `area:db` - Database models, repositories, and queries
- `area:api` - YouTube API integration
- `area:logging` - Logging and observability
- `area:ci` - Continuous Integration and GitHub Actions
- `area:infra` - Infrastructure, Docker, deployment
- `area:devx` - Developer experience and tooling
- `area:bots` - Automated bot configurations

## Priority Labels (priority:*)

Indicates urgency and importance:

- `priority:P0` - Critical - Blocks core functionality, requires immediate attention
- `priority:P1` - High - Important for upcoming release or significantly impacts users
- `priority:P2` - Medium - Should be addressed but not urgent
- `priority:P3` - Low - Nice to have, can be deferred

## Special Labels

- `good first issue` - Good for newcomers to the project
- `help wanted` - Extra attention or external help needed
- `blocked` - Cannot proceed due to dependencies or external factors
- `duplicate` - This issue or PR already exists
- `wontfix` - This will not be worked on
- `invalid` - This doesn't seem right or needs more information

## Usage Guidelines

1. **Every issue should have at least one type label** (type:bug, type:feature, etc.)
2. **Add area labels** to help identify which part of the codebase is involved
3. **Use priority labels** for triaging and planning work
4. **Apply special labels** as needed for community engagement or status tracking

## Applying Labels

Labels are automatically applied by issue templates where possible, but can be manually added or updated during triage. Maintainers should ensure consistent label usage across all issues and PRs.
