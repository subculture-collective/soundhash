#!/bin/bash
#
# Generate all API documentation assets
#
# This script generates:
# - OpenAPI 3.0 specification (JSON/YAML)
# - Postman Collection v2.1
# - Code snippets in multiple languages
#
# Usage:
#   ./scripts/generate_all_docs.sh

set -e  # Exit on error

echo "=================================================="
echo "SoundHash API Documentation Generator"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "scripts/export_openapi.py" ]; then
    echo -e "${RED}❌ Error: Must be run from the repository root${NC}"
    echo "   Current directory: $(pwd)"
    exit 1
fi

# Check Python
if ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Error: Python not found${NC}"
    exit 1
fi

echo -e "${BLUE}📋 Checking dependencies...${NC}"

# Check required Python packages
python -c "import fastapi" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  Warning: FastAPI not installed. Some tools may not work.${NC}"
    echo "   Install with: pip install -r requirements.txt"
}

# Check PyYAML for YAML export
python -c "import yaml" 2>/dev/null && HAS_YAML=1 || {
    echo -e "${YELLOW}⚠️  Warning: PyYAML not installed. YAML export will be skipped.${NC}"
    echo "   Install with: pip install pyyaml"
    HAS_YAML=0
}

echo ""

# 1. Export OpenAPI Specification
echo -e "${BLUE}📤 Step 1: Exporting OpenAPI specification...${NC}"
if python scripts/export_openapi.py --output-dir docs/api 2>&1; then
    echo -e "${GREEN}✅ OpenAPI spec exported${NC}"
else
    echo -e "${YELLOW}⚠️  OpenAPI export encountered warnings (may need dependencies)${NC}"
fi
echo ""

# Check if OpenAPI spec was created
if [ ! -f "docs/api/openapi.json" ]; then
    echo -e "${RED}❌ Error: OpenAPI spec not found. Cannot continue.${NC}"
    echo "   Make sure all dependencies are installed:"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# 2. Generate Postman Collection
echo -e "${BLUE}📮 Step 2: Generating Postman collection...${NC}"
if python scripts/generate_postman.py --openapi docs/api/openapi.json --output-dir docs/api; then
    echo -e "${GREEN}✅ Postman collection generated${NC}"
else
    echo -e "${YELLOW}⚠️  Postman collection generation had warnings${NC}"
fi
echo ""

# 3. Generate Code Snippets
echo -e "${BLUE}💻 Step 3: Generating code snippets...${NC}"
if python scripts/generate_code_snippets.py --output-dir docs/api/code-examples; then
    echo -e "${GREEN}✅ Code snippets generated${NC}"
else
    echo -e "${YELLOW}⚠️  Code snippet generation had warnings${NC}"
fi
echo ""

# Summary
echo "=================================================="
echo -e "${GREEN}✅ Documentation Generation Complete${NC}"
echo "=================================================="
echo ""
echo "Generated files:"
echo "  📄 docs/api/openapi.json          - OpenAPI 3.0 spec (JSON)"
if [ $HAS_YAML -eq 1 ] && [ -f "docs/api/openapi.yaml" ]; then
    echo "  📄 docs/api/openapi.yaml          - OpenAPI 3.0 spec (YAML)"
fi
echo "  📮 docs/api/postman_collection.json - Postman Collection"
echo "  💻 docs/api/code-examples/        - Code snippets"
echo ""
echo "Next steps:"
echo "  1. View interactive docs: http://localhost:8000/docs"
echo "  2. Import Postman collection: docs/api/postman_collection.json"
echo "  3. Review code examples: docs/api/code-examples/"
echo ""
echo "Optional: Generate SDKs (requires openapi-generator-cli)"
echo "  python scripts/generate_sdks.py --languages python,javascript,typescript"
echo ""
