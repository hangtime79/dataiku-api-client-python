#!/bin/bash
#
# Helper script to run integration tests against local Dataiku instance
#
# Usage:
#   ./run_integration_tests.sh                    # Run all integration tests
#   ./run_integration_tests.sh TestRealProjectSync # Run specific test class
#

set -e

# Configuration
DATAIKU_HOST="http://172.18.58.26:10000"
API_KEY_FILE="/opt/dataiku/dss_install/dataiku-claude-api-key.key"
TEST_PROJECT_KEY="AUDIATEAPP"  # Change this to use a different test project

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Dataiku IaC Integration Tests${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if API key file exists
if [ ! -f "$API_KEY_FILE" ]; then
    echo -e "${YELLOW}Warning: API key file not found at $API_KEY_FILE${NC}"
    echo "Please set DATAIKU_API_KEY environment variable manually"
    exit 1
fi

# Read API key
API_KEY=$(cat "$API_KEY_FILE")
echo -e "${GREEN}✓${NC} API key loaded"
echo -e "${GREEN}✓${NC} Dataiku host: $DATAIKU_HOST"
echo -e "${GREEN}✓${NC} Test project: $TEST_PROJECT_KEY"
echo ""

# Export environment variables
export USE_REAL_DATAIKU=true
export DATAIKU_HOST="$DATAIKU_HOST"
export DATAIKU_API_KEY="$API_KEY"
export TEST_PROJECT_KEY="$TEST_PROJECT_KEY"

# Run tests
if [ -z "$1" ]; then
    echo -e "${BLUE}Running all integration tests...${NC}"
    echo ""
    python3 -m pytest tests/iac/integration/ -v
else
    echo -e "${BLUE}Running specific test: $1${NC}"
    echo ""
    python3 -m pytest "tests/iac/integration/test_real_dataiku_sync.py::$1" -v
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Integration tests complete!${NC}"
echo -e "${GREEN}========================================${NC}"
