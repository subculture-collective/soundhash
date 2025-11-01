#!/usr/bin/env python3
"""
Generate Postman Collection from OpenAPI specification.

This script converts the OpenAPI 3.0 spec to a Postman Collection v2.1
format for easy API testing and sharing.

Usage:
    python scripts/generate_postman.py [--output-dir DIR]
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def generate_postman_collection(openapi_spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert OpenAPI specification to Postman Collection v2.1.
    
    Args:
        openapi_spec: OpenAPI 3.0 specification dictionary
        
    Returns:
        Postman Collection v2.1 dictionary
    """
    info = openapi_spec.get("info", {})
    servers = openapi_spec.get("servers", [{"url": "http://localhost:8000"}])
    
    # Create Postman collection structure
    collection = {
        "info": {
            "_postman_id": str(uuid4()),
            "name": info.get("title", "SoundHash API"),
            "description": info.get("description", ""),
            "version": info.get("version", "1.0.0"),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": [],
        "variable": [
            {
                "key": "baseUrl",
                "value": servers[0]["url"],
                "type": "string"
            },
            {
                "key": "access_token",
                "value": "",
                "type": "string"
            },
            {
                "key": "api_key",
                "value": "",
                "type": "string"
            }
        ],
        "auth": {
            "type": "bearer",
            "bearer": [
                {
                    "key": "token",
                    "value": "{{access_token}}",
                    "type": "string"
                }
            ]
        }
    }
    
    # Group endpoints by tags
    tag_groups: Dict[str, List[Dict]] = {}
    
    for path, methods in openapi_spec.get("paths", {}).items():
        for method, operation in methods.items():
            if method.upper() not in ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]:
                continue
                
            tags = operation.get("tags", ["Other"])
            tag = tags[0] if tags else "Other"
            
            if tag not in tag_groups:
                tag_groups[tag] = []
            
            # Build request
            request = {
                "name": operation.get("summary", f"{method.upper()} {path}"),
                "request": {
                    "method": method.upper(),
                    "header": [],
                    "url": {
                        "raw": "{{baseUrl}}" + path,
                        "host": ["{{baseUrl}}"],
                        "path": path.strip("/").split("/")
                    },
                    "description": operation.get("description", "")
                }
            }
            
            # Add headers
            if operation.get("security"):
                request["request"]["header"].append({
                    "key": "Authorization",
                    "value": "Bearer {{access_token}}",
                    "type": "text"
                })
            
            # Add request body if present
            request_body = operation.get("requestBody", {})
            if request_body:
                content = request_body.get("content", {})
                if "application/json" in content:
                    schema = content["application/json"].get("schema", {})
                    example = content["application/json"].get("example", {})
                    
                    request["request"]["body"] = {
                        "mode": "raw",
                        "raw": json.dumps(example or generate_example_from_schema(schema), indent=2),
                        "options": {
                            "raw": {
                                "language": "json"
                            }
                        }
                    }
                    request["request"]["header"].append({
                        "key": "Content-Type",
                        "value": "application/json",
                        "type": "text"
                    })
            
            # Add query parameters
            parameters = operation.get("parameters", [])
            query_params = [p for p in parameters if p.get("in") == "query"]
            if query_params:
                request["request"]["url"]["query"] = [
                    {
                        "key": param["name"],
                        "value": str(param.get("example", "")),
                        "description": param.get("description", ""),
                        "disabled": not param.get("required", False)
                    }
                    for param in query_params
                ]
            
            # Add path parameters
            path_params = [p for p in parameters if p.get("in") == "path"]
            if path_params:
                request["request"]["url"]["variable"] = [
                    {
                        "key": param["name"],
                        "value": str(param.get("example", "1")),
                        "description": param.get("description", "")
                    }
                    for param in path_params
                ]
            
            # Add response examples
            responses = operation.get("responses", {})
            if responses:
                request["response"] = []
                for status_code, response in responses.items():
                    if status_code.startswith("2"):  # Only success responses
                        content = response.get("content", {})
                        if "application/json" in content:
                            example = content["application/json"].get("example", {})
                            request["response"].append({
                                "name": f"Success ({status_code})",
                                "originalRequest": request["request"],
                                "status": response.get("description", "OK"),
                                "code": int(status_code),
                                "_postman_previewlanguage": "json",
                                "header": [
                                    {
                                        "key": "Content-Type",
                                        "value": "application/json"
                                    }
                                ],
                                "body": json.dumps(example, indent=2) if example else ""
                            })
            
            tag_groups[tag].append(request)
    
    # Convert tag groups to folders
    for tag, items in sorted(tag_groups.items()):
        folder = {
            "name": tag,
            "item": items
        }
        
        # Add folder description from tag
        for tag_def in openapi_spec.get("tags", []):
            if tag_def.get("name") == tag:
                folder["description"] = tag_def.get("description", "")
                break
        
        collection["item"].append(folder)
    
    return collection


def generate_example_from_schema(schema: Dict[str, Any]) -> Any:
    """Generate example data from JSON schema."""
    if "example" in schema:
        return schema["example"]
    
    schema_type = schema.get("type", "object")
    
    if schema_type == "object":
        example = {}
        properties = schema.get("properties", {})
        for prop_name, prop_schema in properties.items():
            example[prop_name] = generate_example_from_schema(prop_schema)
        return example
    elif schema_type == "array":
        items = schema.get("items", {})
        return [generate_example_from_schema(items)]
    elif schema_type == "string":
        return schema.get("default", "string")
    elif schema_type == "integer":
        return schema.get("default", 0)
    elif schema_type == "number":
        return schema.get("default", 0.0)
    elif schema_type == "boolean":
        return schema.get("default", False)
    else:
        return None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate Postman Collection from SoundHash OpenAPI specification"
    )
    parser.add_argument(
        "--openapi",
        default="./docs/api/openapi.json",
        help="Path to OpenAPI JSON file"
    )
    parser.add_argument(
        "--output-dir",
        default="./docs/api",
        help="Output directory for Postman collection"
    )
    
    args = parser.parse_args()
    
    # Load OpenAPI spec
    openapi_path = Path(args.openapi)
    if not openapi_path.exists():
        print(f"❌ OpenAPI spec not found: {openapi_path}")
        print("   Run: python scripts/export_openapi.py")
        sys.exit(1)
    
    with open(openapi_path) as f:
        openapi_spec = json.load(f)
    
    print("Generating Postman Collection...")
    collection = generate_postman_collection(openapi_spec)
    
    # Save collection
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    collection_path = output_path / "postman_collection.json"
    with open(collection_path, "w") as f:
        json.dump(collection, f, indent=2)
    
    print(f"✅ Generated Postman Collection: {collection_path}")
    print(f"\n📊 Summary:")
    print(f"   Name: {collection['info']['name']}")
    print(f"   Version: {collection['info']['version']}")
    print(f"   Folders: {len(collection['item'])}")
    print(f"   Total Requests: {sum(len(folder.get('item', [])) for folder in collection['item'])}")
    
    print(f"\n🚀 Import in Postman:")
    print(f"   1. Open Postman")
    print(f"   2. Click Import")
    print(f"   3. Select {collection_path}")
    print(f"   4. Configure variables (baseUrl, access_token, api_key)")


if __name__ == "__main__":
    main()
