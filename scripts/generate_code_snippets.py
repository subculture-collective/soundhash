#!/usr/bin/env python3
"""
Generate code snippets in multiple languages for API endpoints.

This tool generates example code for common API operations in various languages
to help developers get started quickly.

Usage:
    python scripts/generate_code_snippets.py [--output-dir DIR] [--languages LANG1,LANG2]
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List


# Code snippet templates
TEMPLATES = {
    "python": {
        "setup": """from soundhash import ApiClient, Configuration, {api_class}

# Configure API client
config = Configuration()
config.host = "https://api.soundhash.io"
config.access_token = "YOUR_API_TOKEN"

# Create API client
with ApiClient(config) as client:
    api = {api_class}(client)""",
        "list": """    # List {resource}
    {resource} = api.list_{resource}(limit=10)
    
    for item in {resource}:
        print(f"{{item.id}}: {{item.{display_field}}}")""",
        "get": """    # Get {resource}
    {singular} = api.get_{singular}({singular}_id)
    print(f"{singular.capitalize()}: {{{{singular}}.{display_field}}}")""",
        "create": """    # Create {resource}
    {singular} = api.create_{singular}({params})
    print(f"Created {singular}: {{{{singular}}.id}}")""",
        "update": """    # Update {resource}
    {singular} = api.update_{singular}({singular}_id, {params})
    print(f"Updated {singular}: {{{{singular}}.id}}")""",
        "delete": """    # Delete {resource}
    api.delete_{singular}({singular}_id)
    print(f"Deleted {singular}: {{{{singular}_id}}")"""
    },
    "javascript": {
        "setup": """const SoundHash = require('@soundhash/client');

// Configure API client
const client = new SoundHash.ApiClient();
client.basePath = 'https://api.soundhash.io';
client.authentications['bearerAuth'].accessToken = 'YOUR_API_TOKEN';

// Create API instance
const api = new SoundHash.{api_class}(client);""",
        "list": """// List {resource}
api.list{capitalized_resource}({{ limit: 10 }}, (error, data) => {{
  if (error) {{
    console.error(error);
    return;
  }}
  
  data.forEach(item => {{
    console.log(`${{item.id}}: ${{item.{display_field}}}`);
  }});
}});""",
        "get": """// Get {resource}
api.get{capitalized_singular}({singular}Id, (error, {singular}) => {{
  if (error) {{
    console.error(error);
    return;
  }}
  
  console.log(`{singular.capitalize()}: ${{{{singular}}.{display_field}}}`);
}});""",
        "create": """// Create {resource}
api.create{capitalized_singular}({params}, (error, {singular}) => {{
  if (error) {{
    console.error(error);
    return;
  }}
  
  console.log(`Created {singular}: ${{{{singular}}.id}}`);
}});""",
        "update": """// Update {resource}
api.update{capitalized_singular}({singular}Id, {params}, (error, {singular}) => {{
  if (error) {{
    console.error(error);
    return;
  }}
  
  console.log(`Updated {singular}: ${{{{singular}}.id}}`);
}});""",
        "delete": """// Delete {resource}
api.delete{capitalized_singular}({singular}Id, (error) => {{
  if (error) {{
    console.error(error);
    return;
  }}
  
  console.log(`Deleted {singular}: ${{{{singular}Id}}`);
}});"""
    },
    "curl": {
        "list": """# List {resource}
curl -X GET "https://api.soundhash.io/api/v1/{resource}?limit=10" \\
  -H "Authorization: Bearer YOUR_API_TOKEN" \\
  -H "Accept: application/json"
""",
        "get": """# Get {resource}
curl -X GET "https://api.soundhash.io/api/v1/{resource}/{{{singular}_id}}" \\
  -H "Authorization: Bearer YOUR_API_TOKEN" \\
  -H "Accept: application/json"
""",
        "create": """# Create {resource}
curl -X POST "https://api.soundhash.io/api/v1/{resource}" \\
  -H "Authorization: Bearer YOUR_API_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{example_json}'
""",
        "update": """# Update {resource}
curl -X PUT "https://api.soundhash.io/api/v1/{resource}/{{{singular}_id}}" \\
  -H "Authorization: Bearer YOUR_API_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{example_json}'
""",
        "delete": """# Delete {resource}
curl -X DELETE "https://api.soundhash.io/api/v1/{resource}/{{{singular}_id}}" \\
  -H "Authorization: Bearer YOUR_API_TOKEN"
"""
    },
    "php": {
        "setup": """<?php
require_once(__DIR__ . '/vendor/autoload.php');

// Configure API client
$config = SoundHash\\Client\\Configuration::getDefaultConfiguration()
    ->setHost('https://api.soundhash.io')
    ->setAccessToken('YOUR_API_TOKEN');

// Create API instance
$api = new SoundHash\\Client\\Api\\{api_class}(
    new GuzzleHttp\\Client(),
    $config
);
""",
        "list": """// List {resource}
try {{
    ${resource} = $api->list{capitalized_resource}(10);
    foreach (${resource} as $item) {{
        echo $item->getId() . ": " . $item->get{capitalized_display_field}() . "\\n";
    }}
}} catch (Exception $e) {{
    echo 'Error: ' . $e->getMessage();
}}
""",
        "get": """// Get {resource}
try {{
    ${singular} = $api->get{capitalized_singular}(${singular}Id);
    echo "{singular.capitalize()}: " . ${singular}->get{capitalized_display_field}() . "\\n";
}} catch (Exception $e) {{
    echo 'Error: ' . $e->getMessage();
}}
""",
        "create": """// Create {resource}
try {{
    ${singular} = $api->create{capitalized_singular}({params});
    echo "Created {singular}: " . ${singular}->getId() . "\\n";
}} catch (Exception $e) {{
    echo 'Error: ' . $e->getMessage();
}}
""",
        "update": """// Update {resource}
try {{
    ${singular} = $api->update{capitalized_singular}(${singular}Id, {params});
    echo "Updated {singular}: " . ${singular}->getId() . "\\n";
}} catch (Exception $e) {{
    echo 'Error: ' . $e->getMessage();
}}
""",
        "delete": """// Delete {resource}
try {{
    $api->delete{capitalized_singular}(${singular}Id);
    echo "Deleted {singular}: " . ${singular}Id . "\\n";
}} catch (Exception $e) {{
    echo 'Error: ' . $e->getMessage();
}}
"""
    },
    "ruby": {
        "setup": """require 'soundhash'

# Configure API client
SoundHash.configure do |config|
  config.host = 'https://api.soundhash.io'
  config.access_token = 'YOUR_API_TOKEN'
end

# Create API instance
api = SoundHash::{api_class}.new
""",
        "list": """# List {resource}
begin
  {resource} = api.list_{resource}(limit: 10)
  {resource}.each do |item|
    puts "\#{{item.id}}: \#{{item.{display_field}}}"
  end
rescue SoundHash::ApiError => e
  puts "Error: \#{{e}}"
end
""",
        "get": """# Get {resource}
begin
  {singular} = api.get_{singular}({singular}_id)
  puts "{singular.capitalize()}: \#{{{{singular}}.{display_field}}}"
rescue SoundHash::ApiError => e
  puts "Error: \#{{e}}"
end
""",
        "create": """# Create {resource}
begin
  {singular} = api.create_{singular}({params})
  puts "Created {singular}: \#{{{{singular}}.id}}"
rescue SoundHash::ApiError => e
  puts "Error: \#{{e}}"
end
""",
        "update": """# Update {resource}
begin
  {singular} = api.update_{singular}({singular}_id, {params})
  puts "Updated {singular}: \#{{{{singular}}.id}}"
rescue SoundHash::ApiError => e
  puts "Error: \#{{e}}"
end
""",
        "delete": """# Delete {resource}
begin
  api.delete_{singular}({singular}_id)
  puts "Deleted {singular}: \#{{{{singular}_id}}"
rescue SoundHash::ApiError => e
  puts "Error: \#{{e}}"
end
"""
    },
    "go": {
        "setup": """package main

import (
    "context"
    "fmt"
    soundhash "github.com/subculture-collective/soundhash-client-go"
)

func main() {{
    // Configure API client
    config := soundhash.NewConfiguration()
    config.Host = "api.soundhash.io"
    config.Scheme = "https"
    
    client := soundhash.NewAPIClient(config)
    auth := context.WithValue(context.Background(), soundhash.ContextAccessToken, "YOUR_API_TOKEN")
""",
        "list": """    // List {resource}
    {resource}, _, err := client.{api_class}.List{capitalized_resource}(auth).Limit(10).Execute()
    if err != nil {{
        fmt.Println("Error:", err)
        return
    }}
    
    for _, item := range {resource} {{
        fmt.Printf("%d: %s\\n", item.Id, item.{capitalized_display_field})
    }}
""",
        "get": """    // Get {resource}
    {singular}, _, err := client.{api_class}.Get{capitalized_singular}(auth, {singular}Id).Execute()
    if err != nil {{
        fmt.Println("Error:", err)
        return
    }}
    
    fmt.Printf("{singular.capitalize()}: %s\\n", {singular}.{capitalized_display_field})
""",
        "create": """    // Create {resource}
    {singular}, _, err := client.{api_class}.Create{capitalized_singular}(auth).{capitalized_singular}({params}).Execute()
    if err != nil {{
        fmt.Println("Error:", err)
        return
    }}
    
    fmt.Printf("Created {singular}: %d\\n", {singular}.Id)
""",
        "update": """    // Update {resource}
    {singular}, _, err := client.{api_class}.Update{capitalized_singular}(auth, {singular}Id).{capitalized_singular}({params}).Execute()
    if err != nil {{
        fmt.Println("Error:", err)
        return
    }}
    
    fmt.Printf("Updated {singular}: %d\\n", {singular}.Id)
""",
        "delete": """    // Delete {resource}
    _, err := client.{api_class}.Delete{capitalized_singular}(auth, {singular}Id).Execute()
    if err != nil {{
        fmt.Println("Error:", err)
        return
    }}
    
    fmt.Printf("Deleted {singular}: %d\\n", {singular}Id)
}}
"""
    }
}


# Resource configuration
RESOURCES = {
    "videos": {
        "singular": "video",
        "api_class": "VideosApi",
        "display_field": "title",
        "create_params": {"title": "My Video", "url": "https://youtube.com/watch?v=abc123"},
        "update_params": {"title": "Updated Video"}
    },
    "matches": {
        "singular": "match",
        "api_class": "MatchesApi",
        "display_field": "confidence",
        "operations": ["list", "get"]  # No create/update/delete
    },
    "channels": {
        "singular": "channel",
        "api_class": "ChannelsApi",
        "display_field": "title",
        "create_params": {"channel_id": "UCxxx", "title": "My Channel"},
        "update_params": {"title": "Updated Channel"}
    },
    "fingerprints": {
        "singular": "fingerprint",
        "api_class": "FingerprintsApi",
        "display_field": "fingerprint_hash",
        "operations": ["list", "get"]  # No create/update/delete
    },
    "webhooks": {
        "singular": "webhook",
        "api_class": "WebhooksApi",
        "display_field": "url",
        "create_params": {"url": "https://myapp.com/webhook", "events": ["video.processed"]},
        "update_params": {"events": ["video.processed", "match.found"]}
    }
}


def generate_snippets(languages: List[str], output_dir: str):
    """Generate code snippets for all resources and operations."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for resource_name, config in RESOURCES.items():
        singular = config["singular"]
        api_class = config["api_class"]
        display_field = config["display_field"]
        operations = config.get("operations", ["list", "get", "create", "update", "delete"])
        
        # Create resource directory
        resource_dir = output_path / resource_name
        resource_dir.mkdir(parents=True, exist_ok=True)
        
        for language in languages:
            if language not in TEMPLATES:
                print(f"⚠️  Skipping unsupported language: {language}")
                continue
            
            snippets = []
            
            # Add setup if available
            if "setup" in TEMPLATES[language]:
                setup = TEMPLATES[language]["setup"].format(
                    api_class=api_class,
                    resource=resource_name,
                    singular=singular
                )
                snippets.append(setup)
            
            # Add operation snippets
            for operation in operations:
                if operation not in TEMPLATES[language]:
                    continue
                
                # Prepare template variables
                variables = {
                    "resource": resource_name,
                    "singular": singular,
                    "display_field": display_field,
                    "api_class": api_class,
                    "capitalized_resource": resource_name.capitalize(),
                    "capitalized_singular": singular.capitalize(),
                    "capitalized_display_field": display_field.capitalize(),
                }
                
                # Add params for create/update
                if operation == "create" and "create_params" in config:
                    if language == "curl":
                        variables["example_json"] = json.dumps(config["create_params"], indent=2)
                    else:
                        params_list = [f"{k}={repr(v)}" for k, v in config["create_params"].items()]
                        variables["params"] = ", ".join(params_list)
                
                if operation == "update" and "update_params" in config:
                    if language == "curl":
                        variables["example_json"] = json.dumps(config["update_params"], indent=2)
                    else:
                        params_list = [f"{k}={repr(v)}" for k, v in config["update_params"].items()]
                        variables["params"] = ", ".join(params_list)
                
                snippet = TEMPLATES[language][operation].format(**variables)
                snippets.append(snippet)
            
            # Write to file
            extension = "sh" if language == "curl" else language
            if language == "javascript":
                extension = "js"
            elif language == "python":
                extension = "py"
            elif language == "ruby":
                extension = "rb"
            
            output_file = resource_dir / f"{resource_name}.{extension}"
            with open(output_file, "w") as f:
                f.write("\n\n".join(snippets))
            
            print(f"✅ Generated {language} snippets for {resource_name}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate code snippets for SoundHash API"
    )
    parser.add_argument(
        "--languages",
        default="python,javascript,curl,php,ruby,go",
        help="Comma-separated list of languages"
    )
    parser.add_argument(
        "--output-dir",
        default="./docs/api/code-examples",
        help="Output directory for code snippets"
    )
    
    args = parser.parse_args()
    
    languages = [lang.strip() for lang in args.languages.split(",")]
    
    print("Generating code snippets...")
    generate_snippets(languages, args.output_dir)
    
    print(f"\n✅ Code snippets generated in {args.output_dir}")


if __name__ == "__main__":
    main()
