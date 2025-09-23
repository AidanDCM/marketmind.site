#!/bin/bash

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to run a command and check its exit status
run_test() {
    echo -e "${YELLOW}Running: $1${NC}"
    eval $1
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Test failed: $1${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Test passed${NC}\n"
}

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source .venv/bin/activate
fi

# Install test dependencies
echo -e "${YELLOW}Installing test dependencies...${NC}"
pip install -q pytest pytest-cov black flake8 isort mypy locust

# Run linters
echo -e "\n${YELLOW}Running code formatters and linters...${NC}"
run_test "black --check ."
run_test "isort --check-only ."
run_test "flake8 ."
run_test "mypy ."

# Run unit tests
echo -e "\n${YELLOW}Running unit tests...${NC}"
run_test "pytest test_db_models.py -v --cov=packages.shared --cov-report=term-missing"

# Run integration tests
echo -e "\n${YELLOW}Running integration tests...${NC}"
run_test "pytest test_integration.py -v --cov=apps.hive_api --cov-append"

# Run authentication tests
echo -e "\n${YELLOW}Running authentication tests...${NC}"
run_test "pytest test_auth.py -v --cov=apps.hive_api --cov-append"

# Generate coverage report
echo -e "\n${YELLOW}Generating coverage report...${NC}"
python -m pytest --cov=. --cov-report=html --cov-report=xml

# Run performance tests if requested
if [ "$1" == "--performance" ]; then
    echo -e "\n${YELLOW}Running performance tests...${NC}"
    echo -e "${YELLOW}Starting Locust in the background...${NC}"
    locust -f locustfile.py --headless -u 10 -r 1 -t 1m &
    LOCUST_PID=$!
    
    # Give Locust time to start
    sleep 5
    
    # Run a quick test
    echo -e "\n${YELLOW}Running a quick load test...${NC}"
    curl -s "http://localhost:8089/stats/requests" | jq
    
    # Stop Locust
    kill $LOCUST_PID
    wait $LOCUST_PID 2>/dev/null
fi

echo -e "\n${GREEN}🎉 All tests completed successfully!${NC}"
echo -e "${YELLOW}Coverage report: file://$(pwd)/htmlcov/index.html${NC}"

# Open coverage report in default browser
if [ "$1" == "--open" ] || [ "$2" == "--open" ]; then
    open htmlcov/index.html
fi
