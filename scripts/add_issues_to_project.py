#!/usr/bin/env python3
"""
Script to add all repository issues to the GitHub Project board.

This script helps automate the process of adding issues #1-#34 to the 
"@onnwee's soundhash" project board.

Requirements:
- PyGithub library: pip install PyGithub
- GitHub Personal Access Token with 'project' and 'repo' scopes

Usage:
    export GITHUB_TOKEN="your_token_here"
    python scripts/add_issues_to_project.py

Note: This script requires the GitHub Projects (beta) API which uses GraphQL.
You may need to manually add issues via the web interface or use the gh CLI:
    gh project item-add <project-number> --owner @me --url <issue-url>
"""

import os
import sys

def main():
    """Main function to add issues to project board."""
    github_token = os.getenv('GITHUB_TOKEN')
    
    if not github_token:
        print("Error: GITHUB_TOKEN environment variable not set")
        print("\nPlease set your GitHub token:")
        print("  export GITHUB_TOKEN='your_token_here'")
        print("\nYour token needs 'project' and 'repo' scopes.")
        sys.exit(1)
    
    print("GitHub Project Board Integration")
    print("=" * 50)
    print()
    print("The @onnwee's soundhash project board needs to be configured")
    print("to include all issues from this repository.")
    print()
    print("Manual Steps:")
    print("1. Navigate to https://github.com/users/onnwee/projects")
    print("2. Open the '@onnwee's soundhash' project")
    print("3. Click '+' to add items")
    print("4. Search for 'onnwee/soundhash' repository")
    print("5. Select 'Add all issues' or add individually")
    print()
    print("Automated Setup (using gh CLI):")
    print("=" * 50)
    print()
    print("First, get your project number:")
    print("  gh project list --owner @me")
    print()
    print("Then add all issues (replace PROJECT_NUMBER):")
    print("  for i in {1..34}; do")
    print("    gh project item-add PROJECT_NUMBER \\")
    print("      --owner @me \\")
    print("      --url https://github.com/onnwee/soundhash/issues/$i")
    print("  done")
    print()
    print("Configure automation:")
    print("  gh project edit PROJECT_NUMBER \\")
    print("    --owner @me \\")
    print("    --add-item-on-issue-create")
    print()
    print("=" * 50)
    print()
    print("See .github/PROJECT_BOARD_SETUP.md for detailed instructions.")

if __name__ == "__main__":
    main()
