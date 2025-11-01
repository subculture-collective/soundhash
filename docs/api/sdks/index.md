# Official SDKs

SoundHash provides official client libraries in multiple languages to make integration easy. All SDKs are generated from our OpenAPI specification and maintained by the SoundHash team.

## Available SDKs

| Language | Package Manager | Package Name | Status | Documentation |
|----------|----------------|--------------|--------|---------------|
| Python | PyPI | `soundhash-client` | ✅ Stable | [Docs](python.md) |
| JavaScript | npm | `@soundhash/client` | ✅ Stable | [Docs](javascript.md) |
| TypeScript | npm | `@soundhash/client-ts` | ✅ Stable | [Docs](typescript.md) |
| PHP | Packagist | `soundhash/client` | ✅ Stable | [Docs](php.md) |
| Ruby | RubyGems | `soundhash-client` | ✅ Stable | [Docs](ruby.md) |
| Go | GitHub | `github.com/subculture-collective/soundhash-client-go` | ✅ Stable | [Docs](go.md) |

## Quick Comparison

=== "Python"
    ```python
    pip install soundhash-client
    ```
    
    **Best for:** Data science, ML, scripting, backend services
    
    **Features:**
    - Type hints
    - Async support
    - Comprehensive error handling
    - Rich documentation

=== "JavaScript"
    ```bash
    npm install @soundhash/client
    ```
    
    **Best for:** Node.js backends, web applications
    
    **Features:**
    - Promise-based API
    - Callback support
    - Browser and Node.js compatible
    - Lightweight

=== "TypeScript"
    ```bash
    npm install @soundhash/client-ts
    ```
    
    **Best for:** Type-safe JavaScript applications
    
    **Features:**
    - Full type definitions
    - Auto-completion
    - Compile-time safety
    - Modern ES6+ syntax

=== "PHP"
    ```bash
    composer require soundhash/client
    ```
    
    **Best for:** PHP web applications, WordPress plugins
    
    **Features:**
    - PSR-4 autoloading
    - Guzzle HTTP client
    - Comprehensive documentation
    - PHP 7.4+ support

=== "Ruby"
    ```bash
    gem install soundhash-client
    ```
    
    **Best for:** Ruby on Rails applications, scripts
    
    **Features:**
    - Idiomatic Ruby code
    - Faraday HTTP client
    - RSpec tests included
    - Ruby 2.7+ support

=== "Go"
    ```bash
    go get github.com/subculture-collective/soundhash-client-go
    ```
    
    **Best for:** High-performance applications, microservices
    
    **Features:**
    - Native Go types
    - Context support
    - Efficient memory usage
    - Go 1.18+ generics

## Installation

### Python

```bash
pip install soundhash-client

# Or with async support
pip install soundhash-client[async]
```

[View Python Documentation →](python.md)

### JavaScript / TypeScript

```bash
# JavaScript
npm install @soundhash/client

# TypeScript
npm install @soundhash/client-ts
```

[View JavaScript Documentation →](javascript.md) | [View TypeScript Documentation →](typescript.md)

### PHP

```bash
composer require soundhash/client
```

[View PHP Documentation →](php.md)

### Ruby

```bash
gem install soundhash-client

# Or in Gemfile
gem 'soundhash-client'
```

[View Ruby Documentation →](ruby.md)

### Go

```bash
go get github.com/subculture-collective/soundhash-client-go
```

[View Go Documentation →](go.md)

## Common Features

All SDKs provide:

- ✅ **Full API coverage** - All endpoints supported
- ✅ **Authentication** - JWT tokens and API keys
- ✅ **Error handling** - Detailed error messages
- ✅ **Rate limiting** - Built-in rate limit handling
- ✅ **Retries** - Automatic retry with exponential backoff
- ✅ **Logging** - Configurable logging
- ✅ **Testing** - Unit tests included
- ✅ **Documentation** - Comprehensive API docs
- ✅ **Examples** - Code examples for common tasks

## SDK Generation

All SDKs are automatically generated from our OpenAPI specification using [OpenAPI Generator](https://openapi-generator.tech/). This ensures:

- **Consistency** across all languages
- **Up-to-date** with latest API changes
- **Type safety** where applicable
- **Best practices** for each language

To generate SDKs yourself:

```bash
# Export OpenAPI spec
python scripts/export_openapi.py

# Generate SDKs
python scripts/generate_sdks.py
```

## Contributing

Want to improve our SDKs? We welcome contributions!

- [GitHub Repository](https://github.com/subculture-collective/soundhash)
- [Issue Tracker](https://github.com/subculture-collective/soundhash/issues)
- [Contributing Guide](https://github.com/subculture-collective/soundhash/blob/main/CONTRIBUTING.md)

## Support

Need help with an SDK?

- [API Documentation](../index.md)
- [Code Examples](../tutorials/quickstart.md)
- [GitHub Discussions](https://github.com/subculture-collective/soundhash/discussions)
- [Discord Community](https://discord.gg/soundhash)
- [Email Support](mailto:support@soundhash.io)

## Versioning

SDKs follow the same versioning as the API:

- **Major versions** match API major versions (e.g., SDK v1.x for API v1)
- **Minor versions** add new features without breaking changes
- **Patch versions** fix bugs only

Current versions:
- API: v1.0.0
- All SDKs: v1.0.0

## License

All SDKs are open source under the MIT License.
