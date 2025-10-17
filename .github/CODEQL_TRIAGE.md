# CodeQL Security Scanning - Triage Documentation

## Overview

This document tracks CodeQL security findings, false positives, and their resolutions for the SoundHash project.

## Workflow Configuration

- **Triggers**: 
  - Push to `main` branch
  - Pull requests to `main` branch
  - Weekly schedule (Mondays at 00:00 UTC)
- **Language**: Python
- **Results**: Available in the Security tab under Code scanning alerts

## Known False Positives

This section will be updated as CodeQL findings are triaged.

### Template Entry Format

```markdown
### [Alert Type] - [Brief Description]
- **Severity**: [Critical/High/Medium/Low]
- **Location**: [File path and line number]
- **Reason for False Positive**: [Explanation]
- **Mitigation**: [If applicable, what makes this safe]
- **Date Triaged**: [YYYY-MM-DD]
- **Triaged By**: [GitHub username]
```

## Security Best Practices

The following practices are followed to minimize security vulnerabilities:

1. **Input Validation**: All external inputs (URLs, API data) are validated before processing
2. **Dependency Management**: Regular updates via `requirements.txt` with pinned versions
3. **Secret Management**: Sensitive data stored in environment variables, never committed
4. **Database Security**: Using parameterized queries via SQLAlchemy ORM
5. **API Authentication**: OAuth flows for YouTube API, secure token storage

## Reviewing Alerts

When new CodeQL alerts are generated:

1. Navigate to the Security tab in the GitHub repository
2. Review the alert details and code location
3. Determine if it's a true positive or false positive
4. For false positives: Document here with justification
5. For true positives: Create an issue and fix the vulnerability
6. Use CodeQL's suppression comments only when absolutely necessary and documented

## Resources

- [CodeQL Documentation](https://codeql.github.com/docs/)
- [GitHub Code Scanning](https://docs.github.com/en/code-security/code-scanning)
- [Python CodeQL Queries](https://codeql.github.com/codeql-query-help/python/)
