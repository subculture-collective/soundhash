# Developer Tools Guide

This guide explains how to use the developer tools to generate API documentation, SDKs, and code examples.

## Overview

SoundHash provides several tools to help developers integrate with the API:

1. **OpenAPI Specification Export** - Generate OpenAPI 3.0 spec
2. **Postman Collection Generator** - Create importable Postman collection
3. **Multi-Language SDK Generator** - Generate client libraries
4. **Webhook Testing Tool** - Test webhook endpoints
5. **Code Snippet Generator** - Generate code examples

## Prerequisites

### Python Environment

Install required dependencies:

```bash
# Core dependencies
pip install -r requirements.txt

# Optional: For YAML export
pip install pyyaml

# Optional: For SDK generation (if using npx)
npm install -g @openapitools/openapi-generator-cli

# Or use Docker for SDK generation
docker pull openapitools/openapi-generator-cli
```

## Tool Usage

### 1. Export OpenAPI Specification

Generate OpenAPI 3.0 specification in JSON and YAML formats:

```bash
python scripts/export_openapi.py --output-dir ./docs/api
```

**Output:**
- `docs/api/openapi.json` - OpenAPI spec in JSON
- `docs/api/openapi.yaml` - OpenAPI spec in YAML (requires PyYAML)
- `docs/api/openapi-v1.0.0.json` - Versioned spec

**Options:**
- `--output-dir DIR` - Output directory (default: `./docs/api`)

**Use Cases:**
- Publishing API specification
- SDK generation
- API documentation tools
- Contract testing

### 2. Generate Postman Collection

Convert OpenAPI spec to Postman Collection v2.1:

```bash
# First export OpenAPI spec
python scripts/export_openapi.py

# Then generate Postman collection
python scripts/generate_postman.py --openapi ./docs/api/openapi.json
```

**Output:**
- `docs/api/postman_collection.json` - Importable Postman collection

**Options:**
- `--openapi FILE` - Path to OpenAPI JSON (default: `./docs/api/openapi.json`)
- `--output-dir DIR` - Output directory (default: `./docs/api`)

**Features:**
- All endpoints organized by tags
- Authentication configuration
- Request/response examples
- Environment variables for base URL and tokens

**Import to Postman:**
1. Open Postman
2. Click **Import**
3. Select `postman_collection.json`
4. Configure variables:
   - `baseUrl` - API endpoint (default: http://localhost:8000)
   - `access_token` - Your API token
   - `api_key` - Your API key

### 3. Generate Multi-Language SDKs

Generate client SDKs in multiple languages:

```bash
# Generate all supported SDKs
python scripts/generate_sdks.py

# Generate specific languages
python scripts/generate_sdks.py --languages python,javascript,typescript

# Use Docker instead of npm
python scripts/generate_sdks.py --use-docker
```

**Supported Languages:**
- Python (`python`)
- JavaScript (`javascript`)
- TypeScript (`typescript`)
- PHP (`php`)
- Ruby (`ruby`)
- Go (`go`)

**Output Structure:**
```
client-sdk/
├── python/          # Python SDK
│   ├── soundhash/
│   ├── setup.py
│   └── README.md
├── javascript/      # JavaScript SDK
│   ├── src/
│   ├── package.json
│   └── README.md
├── typescript/      # TypeScript SDK
│   ├── src/
│   ├── package.json
│   └── README.md
├── php/            # PHP SDK
│   ├── src/
│   ├── composer.json
│   └── README.md
├── ruby/           # Ruby SDK
│   ├── lib/
│   ├── soundhash-client.gemspec
│   └── README.md
└── go/             # Go SDK
    ├── soundhash/
    ├── go.mod
    └── README.md
```

**Options:**
- `--languages LANGS` - Comma-separated list of languages
- `--openapi FILE` - Path to OpenAPI JSON
- `--output-dir DIR` - Base output directory
- `--use-docker` - Use Docker instead of CLI tool

**Requirements:**

Option 1: NPM (Recommended)
```bash
npm install -g @openapitools/openapi-generator-cli
```

Option 2: Docker
```bash
docker pull openapitools/openapi-generator-cli
python scripts/generate_sdks.py --use-docker
```

**Publishing SDKs:**

After generation, test and publish to package managers:

```bash
# Python - PyPI
cd client-sdk/python
python setup.py sdist bdist_wheel
twine upload dist/*

# JavaScript - npm
cd client-sdk/javascript
npm publish

# TypeScript - npm
cd client-sdk/typescript
npm publish

# PHP - Packagist
# Push to GitHub and submit to packagist.org

# Ruby - RubyGems
cd client-sdk/ruby
gem build *.gemspec
gem push *.gem

# Go - GitHub
# Push to github.com/subculture-collective/soundhash-client-go
```

### 4. Test Webhooks

Test webhook endpoints with sample events:

```bash
# Test with sample event
python scripts/test_webhook.py \
  --url https://myapp.com/webhooks/soundhash \
  --event video.processed \
  --secret my-webhook-secret

# Test with custom data
python scripts/test_webhook.py \
  --url http://localhost:3000/webhook \
  --event match.found \
  --secret test-secret \
  --custom-data '{"query_id": "test123"}'
```

**Available Events:**
- `video.uploaded` - Video uploaded
- `video.processing` - Processing started
- `video.processed` - Processing completed
- `video.failed` - Processing failed
- `match.found` - Match detected
- `fingerprint.created` - Fingerprint extracted
- `channel.ingested` - Channel ingestion completed
- `quota.warning` - Approaching quota limit

**Options:**
- `--url URL` - Webhook endpoint URL (required)
- `--event TYPE` - Event type (required)
- `--secret SECRET` - Webhook secret for signature (required)
- `--custom-data JSON` - Custom JSON data (overrides sample)
- `--webhook-id ID` - Webhook ID (default: wh_test123)
- `--delivery-id ID` - Delivery ID (auto-generated)

**Features:**
- HMAC SHA-256 signature generation
- Sample payloads for all event types
- Response verification
- Timing metrics

**Local Testing with ngrok:**
```bash
# Start ngrok
ngrok http 3000

# Test with ngrok URL
python scripts/test_webhook.py \
  --url https://abc123.ngrok.io/webhooks \
  --event video.processed \
  --secret test-secret
```

### 5. Generate Code Snippets

Generate code examples for common operations:

```bash
# Generate all examples
python scripts/generate_code_snippets.py

# Generate specific languages
python scripts/generate_code_snippets.py --languages python,javascript,curl
```

**Output Structure:**
```
docs/api/code-examples/
├── videos/
│   ├── videos.py        # Python examples
│   ├── videos.js        # JavaScript examples
│   ├── videos.sh        # cURL examples
│   ├── videos.php       # PHP examples
│   ├── videos.rb        # Ruby examples
│   └── videos.go        # Go examples
├── matches/
│   └── ...
└── channels/
    └── ...
```

**Supported Languages:**
- Python
- JavaScript
- cURL
- PHP
- Ruby
- Go

**Options:**
- `--languages LANGS` - Comma-separated list of languages
- `--output-dir DIR` - Output directory (default: `./docs/api/code-examples`)

**Use Cases:**
- Documentation examples
- Tutorial content
- Copy-paste snippets for developers
- Testing reference implementations

## Automation Workflows

### Complete Documentation Generation

Generate all documentation assets:

```bash
#!/bin/bash

# 1. Export OpenAPI spec
echo "Exporting OpenAPI specification..."
python scripts/export_openapi.py

# 2. Generate Postman collection
echo "Generating Postman collection..."
python scripts/generate_postman.py

# 3. Generate code snippets
echo "Generating code snippets..."
python scripts/generate_code_snippets.py

# 4. Generate SDKs (optional - requires openapi-generator)
echo "Generating SDKs..."
python scripts/generate_sdks.py --languages python,javascript,typescript

echo "✅ Documentation generation complete!"
```

Save as `scripts/generate_all_docs.sh` and run:

```bash
chmod +x scripts/generate_all_docs.sh
./scripts/generate_all_docs.sh
```

### CI/CD Integration

Add to your GitHub Actions workflow:

```yaml
name: Generate API Documentation

on:
  push:
    branches: [main]
    paths:
      - 'src/api/**'
      - 'docs/api/**'

jobs:
  generate-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pyyaml
      
      - name: Generate OpenAPI spec
        run: python scripts/export_openapi.py
      
      - name: Generate Postman collection
        run: python scripts/generate_postman.py
      
      - name: Generate code snippets
        run: python scripts/generate_code_snippets.py
      
      - name: Commit changes
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add docs/api/
          git commit -m "Update API documentation" || echo "No changes"
          git push
```

## Best Practices

### 1. Version Control

- Commit generated OpenAPI specs to version control
- Keep Postman collections in the repo for easy sharing
- Exclude generated SDK code from main repo (create separate repos)

### 2. Documentation Updates

- Regenerate docs after API changes
- Update changelog with breaking changes
- Version OpenAPI specs with each release

### 3. SDK Distribution

- Test SDKs before publishing
- Follow semantic versioning
- Maintain separate repos for each language
- Auto-generate on API version releases

### 4. Webhook Testing

- Test webhooks during development with ngrok
- Verify signature validation
- Test all event types
- Monitor webhook logs in production

### 5. Code Examples

- Keep examples simple and focused
- Test examples before publishing
- Update examples with API changes
- Include error handling in examples

## Troubleshooting

### OpenAPI Export Fails

**Error:** `ModuleNotFoundError`

**Solution:** Install all dependencies:
```bash
pip install -r requirements.txt
```

### SDK Generation Fails

**Error:** `openapi-generator-cli: command not found`

**Solution:** Install generator or use Docker:
```bash
npm install -g @openapitools/openapi-generator-cli
# OR
python scripts/generate_sdks.py --use-docker
```

### Webhook Test Fails

**Error:** Connection refused

**Solution:**
- Verify endpoint is accessible
- Check firewall rules
- Use ngrok for local testing
- Verify SSL certificate (for HTTPS)

### Code Generation Incomplete

**Error:** Missing templates

**Solution:**
- Update script to add missing language
- Check template syntax
- Verify resource configuration

## Support

Need help with developer tools?

- [GitHub Issues](https://github.com/subculture-collective/soundhash/issues)
- [Discord Community](https://discord.gg/soundhash)
- [Email Support](mailto:support@soundhash.io)
- [API Documentation](index.md)
