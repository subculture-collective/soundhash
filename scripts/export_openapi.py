#!/usr/bin/env python3
"""
Export OpenAPI 3.0 specification from FastAPI application.

This script generates the OpenAPI spec in both JSON and YAML formats
for use with API documentation, SDK generation, and Postman collections.

Usage:
    python scripts/export_openapi.py [--output-dir DIR]
"""

import argparse
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.main import app


def export_openapi(output_dir: str = "./docs/api"):
    """
    Export OpenAPI specification to JSON and YAML files.
    
    Args:
        output_dir: Directory to save the specification files
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Get OpenAPI schema
    openapi_schema = app.openapi()
    
    # Add additional metadata for developer portal
    openapi_schema["info"]["x-logo"] = {
        "url": "https://raw.githubusercontent.com/subculture-collective/soundhash/main/docs/assets/logo.png",
        "altText": "SoundHash Logo"
    }
    
    openapi_schema["info"]["contact"] = {
        "name": "SoundHash Support",
        "url": "https://github.com/subculture-collective/soundhash/issues",
        "email": "support@soundhash.io"
    }
    
    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://github.com/subculture-collective/soundhash/blob/main/LICENSE"
    }
    
    # Add server information
    openapi_schema["servers"] = [
        {
            "url": "https://api.soundhash.io",
            "description": "Production server"
        },
        {
            "url": "https://staging.api.soundhash.io",
            "description": "Staging server"
        },
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        }
    ]
    
    # Add external documentation
    openapi_schema["externalDocs"] = {
        "description": "Full API Documentation",
        "url": "https://docs.soundhash.io/api"
    }
    
    # Add tags descriptions
    openapi_schema["tags"] = [
        {
            "name": "Authentication",
            "description": "User authentication, registration, and API key management"
        },
        {
            "name": "Videos",
            "description": "Upload, process, and manage videos"
        },
        {
            "name": "Matches",
            "description": "Find audio matches and search clips"
        },
        {
            "name": "Channels",
            "description": "YouTube channel management and ingestion"
        },
        {
            "name": "Fingerprints",
            "description": "Audio fingerprint operations"
        },
        {
            "name": "Admin",
            "description": "System administration and monitoring"
        },
        {
            "name": "Webhooks",
            "description": "Webhook configuration and management"
        },
        {
            "name": "Analytics",
            "description": "API usage analytics and metrics"
        },
        {
            "name": "Monitoring",
            "description": "System health and performance monitoring"
        },
        {
            "name": "Billing",
            "description": "Billing and subscription management"
        }
    ]
    
    # Export as JSON
    json_path = output_path / "openapi.json"
    with open(json_path, "w") as f:
        json.dump(openapi_schema, f, indent=2)
    print(f"✅ Exported OpenAPI spec to {json_path}")
    
    # Export as YAML (requires PyYAML)
    try:
        import yaml
        yaml_path = output_path / "openapi.yaml"
        with open(yaml_path, "w") as f:
            yaml.dump(openapi_schema, f, default_flow_style=False, sort_keys=False)
        print(f"✅ Exported OpenAPI spec to {yaml_path}")
    except ImportError:
        print("⚠️  PyYAML not installed. Skipping YAML export.")
        print("   Install with: pip install pyyaml")
    
    # Create a version-specific copy
    version = openapi_schema["info"]["version"]
    versioned_json = output_path / f"openapi-v{version}.json"
    with open(versioned_json, "w") as f:
        json.dump(openapi_schema, f, indent=2)
    print(f"✅ Exported versioned spec to {versioned_json}")
    
    return openapi_schema


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Export OpenAPI 3.0 specification from SoundHash API"
    )
    parser.add_argument(
        "--output-dir",
        default="./docs/api",
        help="Output directory for OpenAPI files (default: ./docs/api)"
    )
    
    args = parser.parse_args()
    
    print("Exporting OpenAPI specification...")
    schema = export_openapi(args.output_dir)
    
    print(f"\n📊 Summary:")
    print(f"   Title: {schema['info']['title']}")
    print(f"   Version: {schema['info']['version']}")
    print(f"   Endpoints: {sum(len(methods) for methods in schema['paths'].values())}")
    print(f"   Tags: {len(schema.get('tags', []))}")
    
    print(f"\n🚀 Next steps:")
    print(f"   1. View interactive docs: http://localhost:8000/docs")
    print(f"   2. Generate SDKs: python scripts/generate_sdks.py")
    print(f"   3. Create Postman collection: python scripts/generate_postman.py")


if __name__ == "__main__":
    main()
