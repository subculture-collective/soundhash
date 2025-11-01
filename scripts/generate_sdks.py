#!/usr/bin/env python3
"""
Generate client SDKs in multiple languages from OpenAPI specification.

This script uses OpenAPI Generator to create SDKs for:
- Python
- JavaScript/TypeScript
- PHP
- Ruby
- Go

Usage:
    python scripts/generate_sdks.py [--languages LANG1,LANG2] [--output-dir DIR]
    
Requirements:
    - openapi-generator-cli (via npm or docker)
    - Install: npm install -g @openapitools/openapi-generator-cli
    - Or use Docker: docker pull openapitools/openapi-generator-cli
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Constants
MAX_ERROR_OUTPUT_LENGTH = 500  # Maximum length of error output to display


SUPPORTED_LANGUAGES = {
    "python": {
        "generator": "python",
        "output_dir": "client-sdk/python",
        "package_name": "soundhash-client",
        "additional_properties": {
            "packageName": "soundhash",
            "projectName": "soundhash-client",
            "packageVersion": "1.0.0",
            "packageUrl": "https://github.com/subculture-collective/soundhash",
        }
    },
    "javascript": {
        "generator": "javascript",
        "output_dir": "client-sdk/javascript",
        "package_name": "@soundhash/client",
        "additional_properties": {
            "projectName": "soundhash-client",
            "moduleName": "SoundHashClient",
            "projectVersion": "1.0.0",
            "licenseName": "MIT",
        }
    },
    "typescript": {
        "generator": "typescript-axios",
        "output_dir": "client-sdk/typescript",
        "package_name": "@soundhash/client-ts",
        "additional_properties": {
            "npmName": "@soundhash/client-ts",
            "npmVersion": "1.0.0",
            "supportsES6": "true",
        }
    },
    "php": {
        "generator": "php",
        "output_dir": "client-sdk/php",
        "package_name": "soundhash/client",
        "additional_properties": {
            "packageName": "SoundHash\\Client",
            "invokerPackage": "SoundHash\\Client",
            "composerProjectName": "soundhash/client",
        }
    },
    "ruby": {
        "generator": "ruby",
        "output_dir": "client-sdk/ruby",
        "package_name": "soundhash-client",
        "additional_properties": {
            "gemName": "soundhash-client",
            "moduleName": "SoundHash",
            "gemVersion": "1.0.0",
            "gemHomepage": "https://github.com/subculture-collective/soundhash",
        }
    },
    "go": {
        "generator": "go",
        "output_dir": "client-sdk/go",
        "package_name": "github.com/subculture-collective/soundhash-client-go",
        "additional_properties": {
            "packageName": "soundhash",
            "packageVersion": "1.0.0",
        }
    }
}


def check_openapi_generator() -> bool:
    """Check if openapi-generator-cli is available."""
    try:
        result = subprocess.run(
            ["openapi-generator-cli", "version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False  # Don't raise on non-zero exit
        )
        if result.returncode == 0:
            print(f"✅ Found openapi-generator-cli: {result.stdout.strip()}")
            return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        # It's expected that this may fail if openapi-generator-cli is not installed;
        # we'll try using npx as a fallback below.
        pass
    
    # Try npx
    try:
        result = subprocess.run(
            ["npx", "@openapitools/openapi-generator-cli", "version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"✅ Found openapi-generator-cli via npx")
            return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        # Neither direct CLI nor npx found; return False to indicate unavailability
        pass
    
    return False


def generate_sdk(
    language: str,
    openapi_spec_path: str,
    output_base_dir: str,
    use_docker: bool = False
) -> bool:
    """
    Generate SDK for a specific language.
    
    Args:
        language: Target language/generator
        openapi_spec_path: Path to OpenAPI specification
        output_base_dir: Base directory for SDK output
        use_docker: Use Docker instead of CLI tool
        
    Returns:
        True if successful, False otherwise
    """
    if language not in SUPPORTED_LANGUAGES:
        print(f"❌ Unsupported language: {language}")
        return False
    
    config = SUPPORTED_LANGUAGES[language]
    output_dir = Path(output_base_dir) / config["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Build additional properties string
    additional_props = ",".join(
        f"{k}={v}" for k, v in config["additional_properties"].items()
    )
    
    # Build command
    if use_docker:
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{Path.cwd()}:/local",
            "openapitools/openapi-generator-cli",
            "generate",
            "-i", f"/local/{openapi_spec_path}",
            "-g", config["generator"],
            "-o", f"/local/{output_dir}",
        ]
    else:
        # Try direct CLI first, fallback to npx
        try:
            result = subprocess.run(
                ["openapi-generator-cli", "version"], 
                capture_output=True, 
                timeout=5, 
                check=False
            )
            if result.returncode == 0:
                base_cmd = ["openapi-generator-cli"]
            else:
                base_cmd = ["npx", "@openapitools/openapi-generator-cli"]
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            # Fallback to npx if CLI not found
            base_cmd = ["npx", "@openapitools/openapi-generator-cli"]
        
        cmd = [
            *base_cmd,
            "generate",
            "-i", openapi_spec_path,
            "-g", config["generator"],
            "-o", str(output_dir),
        ]
    
    if additional_props:
        cmd.extend(["--additional-properties", additional_props])
    
    # Note: --package-name flag is not supported by all generators
    # Package name is typically handled via --additional-properties
    # Keeping this for backwards compatibility, but it may be ignored by some generators
    
    print(f"\n🔨 Generating {language.upper()} SDK...")
    print(f"   Output: {output_dir}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            print(f"✅ Successfully generated {language} SDK")
            
            # Create README for the SDK
            create_sdk_readme(language, output_dir, config)
            return True
        else:
            print(f"❌ Failed to generate {language} SDK")
            print(f"   Return code: {result.returncode}")
            if result.stderr:
                print(f"   Error: {result.stderr[:MAX_ERROR_OUTPUT_LENGTH]}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"❌ Timeout generating {language} SDK")
        return False
    except Exception as e:
        print(f"❌ Error generating {language} SDK: {e}")
        return False


def create_sdk_readme(language: str, output_dir: Path, config: dict):
    """Create a README for the generated SDK."""
    readme_content = f"""# SoundHash {language.capitalize()} SDK

Official {language.capitalize()} client library for the SoundHash API.

## Installation

"""
    
    if language == "python":
        readme_content += """```bash
pip install soundhash-client
```

## Quick Start

```python
from soundhash import ApiClient, Configuration, VideosApi

# Configure API client
config = Configuration()
config.host = "https://api.soundhash.io"
config.access_token = "YOUR_API_TOKEN"

# Create API client
with ApiClient(config) as client:
    api = VideosApi(client)
    videos = api.list_videos(limit=10)
    
    for video in videos:
        print(f"{video.title} - {video.duration}s")
```
"""
    elif language in ["javascript", "typescript"]:
        readme_content += """```bash
npm install @soundhash/client
```

## Quick Start

```javascript
const SoundHash = require('@soundhash/client');

const client = new SoundHash.ApiClient();
client.basePath = 'https://api.soundhash.io';
client.authentications['bearerAuth'].accessToken = 'YOUR_API_TOKEN';

const videosApi = new SoundHash.VideosApi(client);

videosApi.listVideos({ limit: 10 }, (error, data) => {
  if (error) {
    console.error(error);
  } else {
    data.forEach(video => {
      console.log(`${video.title} - ${video.duration}s`);
    });
  }
});
```
"""
    elif language == "php":
        readme_content += """```bash
composer require soundhash/client
```

## Quick Start

```php
<?php
require_once(__DIR__ . '/vendor/autoload.php');

$config = SoundHash\\Client\\Configuration::getDefaultConfiguration()
    ->setHost('https://api.soundhash.io')
    ->setAccessToken('YOUR_API_TOKEN');

$apiInstance = new SoundHash\\Client\\Api\\VideosApi(
    new GuzzleHttp\\Client(),
    $config
);

try {
    $result = $apiInstance->listVideos(10);
    foreach ($result as $video) {
        echo $video->getTitle() . " - " . $video->getDuration() . "s\\n";
    }
} catch (Exception $e) {
    echo 'Error: ' . $e->getMessage();
}
?>
```
"""
    elif language == "ruby":
        readme_content += """```bash
gem install soundhash-client
```

## Quick Start

```ruby
require 'soundhash'

SoundHash.configure do |config|
  config.host = 'https://api.soundhash.io'
  config.access_token = 'YOUR_API_TOKEN'
end

api_instance = SoundHash::VideosApi.new

begin
  result = api_instance.list_videos(limit: 10)
  result.each do |video|
    puts "#{video.title} - #{video.duration}s"
  end
rescue SoundHash::ApiError => e
  puts "Error: #{e}"
end
```
"""
    elif language == "go":
        readme_content += """```bash
go get github.com/subculture-collective/soundhash-client-go
```

## Quick Start

```go
package main

import (
    "context"
    "fmt"
    soundhash "github.com/subculture-collective/soundhash-client-go"
)

func main() {
    config := soundhash.NewConfiguration()
    config.Host = "api.soundhash.io"
    config.Scheme = "https"
    
    client := soundhash.NewAPIClient(config)
    auth := context.WithValue(context.Background(), soundhash.ContextAccessToken, "YOUR_API_TOKEN")
    
    videos, _, err := client.VideosApi.ListVideos(auth).Limit(10).Execute()
    if err != nil {
        fmt.Println("Error:", err)
        return
    }
    
    for _, video := range videos {
        fmt.Printf("%s - %ds\\n", video.Title, video.Duration)
    }
}
```
"""
    
    readme_content += f"""
## Documentation

- [API Documentation](https://docs.soundhash.io/api)
- [SDK Reference]({output_dir}/docs)
- [Examples]({output_dir}/examples)

## Authentication

The SoundHash API uses Bearer token authentication. Get your API token from the [developer portal](https://docs.soundhash.io/api/authentication).

## Support

- [GitHub Issues](https://github.com/subculture-collective/soundhash/issues)
- [API Status](https://status.soundhash.io)
- [Developer Portal](https://docs.soundhash.io)

## License

MIT License - see LICENSE file for details
"""
    
    readme_path = output_dir / "README.md"
    with open(readme_path, "w") as f:
        f.write(readme_content)
    
    print(f"   Created README: {readme_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate client SDKs for SoundHash API"
    )
    parser.add_argument(
        "--languages",
        default="python,javascript,typescript,php,ruby,go",
        help="Comma-separated list of languages to generate (default: all)"
    )
    parser.add_argument(
        "--openapi",
        default="./docs/api/openapi.json",
        help="Path to OpenAPI JSON file"
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Base output directory for SDKs"
    )
    parser.add_argument(
        "--use-docker",
        action="store_true",
        help="Use Docker instead of CLI tool"
    )
    
    args = parser.parse_args()
    
    # Check OpenAPI spec exists
    openapi_path = Path(args.openapi)
    if not openapi_path.exists():
        print(f"❌ OpenAPI spec not found: {openapi_path}")
        print("   Run: python scripts/export_openapi.py")
        sys.exit(1)
    
    # Check if generator is available
    if not args.use_docker and not check_openapi_generator():
        print("\n❌ openapi-generator-cli not found")
        print("\nInstall options:")
        print("  1. npm install -g @openapitools/openapi-generator-cli")
        print("  2. Use --use-docker flag (requires Docker)")
        sys.exit(1)
    
    # Parse languages
    languages = [lang.strip() for lang in args.languages.split(",")]
    
    print(f"\n🚀 Generating SDKs for: {', '.join(languages)}")
    print(f"   OpenAPI spec: {openapi_path}")
    print(f"   Output dir: {args.output_dir}\n")
    
    # Generate SDKs
    results = {}
    for language in languages:
        if language not in SUPPORTED_LANGUAGES:
            print(f"⚠️  Skipping unsupported language: {language}")
            continue
        
        success = generate_sdk(
            language,
            str(openapi_path),
            args.output_dir,
            args.use_docker
        )
        results[language] = success
    
    # Print summary
    print("\n" + "="*60)
    print("📊 Generation Summary")
    print("="*60)
    
    for language, success in results.items():
        status = "✅ Success" if success else "❌ Failed"
        print(f"  {language.ljust(15)} {status}")
    
    successful = sum(1 for s in results.values() if s)
    total = len(results)
    
    print("\n" + f"Generated {successful}/{total} SDKs successfully")
    
    if successful > 0:
        print("\n🎉 Next steps:")
        print("  1. Test the generated SDKs")
        print("  2. Publish to package managers:")
        for lang in results:
            if results[lang]:
                config = SUPPORTED_LANGUAGES[lang]
                if lang == "python":
                    print(f"     - PyPI: cd {config['output_dir']} && python setup.py sdist && twine upload dist/*")
                elif lang in ["javascript", "typescript"]:
                    print(f"     - npm: cd {config['output_dir']} && npm publish")
                elif lang == "php":
                    print(f"     - Packagist: Create repo and submit to packagist.org")
                elif lang == "ruby":
                    print(f"     - RubyGems: cd {config['output_dir']} && gem build *.gemspec && gem push *.gem")
                elif lang == "go":
                    print(f"     - GitHub: Push to github.com/subculture-collective/soundhash-client-go")
    
    sys.exit(0 if successful == total else 1)


if __name__ == "__main__":
    main()
