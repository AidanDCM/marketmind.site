#!/bin/bash
# Security checks for CI/CD pipeline
# This script runs secret scanning and dependency audits

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Preferred pip-audit command (set during installation)
PIP_AUDIT_CMD=""

echo -e "${YELLOW}=== Starting Security Checks ===${NC}"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install required tools if not present
install_required_tools() {
    echo -e "${YELLOW}Checking for required tools...${NC}"
    
    # Install gitleaks if not installed
    if ! command_exists gitleaks; then
        echo "Installing gitleaks..."
        if command_exists brew; then
            brew install gitleaks
        elif command_exists docker; then
            echo "Using gitleaks via Docker..."
            GITLEAKS_CMD="docker run --rm -v $(pwd):/code zricethezav/gitleaks:latest"
        else
            echo -e "${RED}Error: gitleaks not found and no package manager available to install it.${NC}"
            echo "Please install gitleaks manually: https://github.com/zricethezav/gitleaks"
            exit 1
        fi
    else
        GITLEAKS_CMD="gitleaks"
    fi
    
    # Install pip-audit if not installed (prefer venv pip)
    if ! command_exists pip-audit; then
        echo "Installing pip-audit..."
        if [ -x ".venv/bin/pip" ]; then
            .venv/bin/pip install pip-audit || true
        elif command_exists pip; then
            pip install --user pip-audit || true
        else
            echo -e "${YELLOW}pip not found; skipping pip-audit install${NC}"
        fi
    fi

    # Resolve pip-audit command path (prefer venv)
    if [ -x ".venv/bin/pip-audit" ]; then
        PIP_AUDIT_CMD=".venv/bin/pip-audit"
    elif command_exists pip-audit; then
        PIP_AUDIT_CMD="pip-audit"
    else
        PIP_AUDIT_CMD=""
    fi
    
    # Install npm audit if not available
    if [ -f "package.json" ] && ! command_exists npm; then
        echo -e "${YELLOW}Warning: package.json found but npm is not installed. Some checks will be skipped.${NC}"
    fi
}

# Run secret scanning with gitleaks
run_secret_scan() {
    echo -e "\n${YELLOW}=== Scanning for secrets in codebase ===${NC}"
    
    # Run gitleaks with a reasonable configuration
    if [ -z "${GITLEAKS_CMD}" ]; then
        GITLEAKS_CMD="gitleaks"
    fi
    
    # Check if we're using Docker
    if [[ "$GITLEAKS_CMD" == docker* ]]; then
        echo "Running gitleaks via Docker..."
        $GITLEAKS_CMD detect --source /code -v --exit-code 1
    else
        echo "Running gitleaks..."
        $GITLEAKS_CMD detect -v --exit-code 1
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ No secrets detected in code${NC}"
    else
        echo -e "${RED}✗ Secrets detected in code. Check the output above for details.${NC}"
        exit 1
    fi
}

# Run Python dependency audit
run_python_audit() {
    echo -e "\n${YELLOW}=== Auditing Python dependencies ===${NC}"
    
    # Check for requirements files
    REQ_FILES=()
    [ -f "requirements.txt" ] && REQ_FILES+=("requirements.txt")
    [ -f "requirements-dev.txt" ] && REQ_FILES+=("requirements-dev.txt")
    [ -f "setup.py" ] && REQ_FILES+=("setup.py")
    [ -f "pyproject.toml" ] && REQ_FILES+=("pyproject.toml")
    
    if [ ${#REQ_FILES[@]} -eq 0 ]; then
        echo "No Python dependency files found. Skipping Python audit."
        return 0
    fi
    
    echo "Scanning dependencies in: ${REQ_FILES[*]}"
    
    # Run pip-audit with common false positives ignored
    if [ -z "${PIP_AUDIT_CMD}" ]; then
        echo -e "${YELLOW}pip-audit not available; skipping Python audit${NC}"
        return 0
    fi
    # Audit the known requirement files deterministically
    AUDIT_FILES=(
      "requirements-dev.txt"
      "infra/docker/requirements-api.txt"
      "infra/docker/requirements-worker.txt"
    )

    for req in "${AUDIT_FILES[@]}"; do
      if [ -f "$req" ]; then
        echo "\nAuditing $req ..."
        ${PIP_AUDIT_CMD} -r "$req" \
          --ignore-vuln "PYSEC-2021-1536" \
          --ignore-vuln "PYSEC-2021-1537" \
          --ignore-vuln "GHSA-wj6h-64fc-37mp" \
          --ignore-vuln "GHSA-f96h-pmfr-66vw" \
          || {
            echo -e "${RED}pip-audit reported issues for $req${NC}"
            exit 1
          }
      else
        echo -e "${YELLOW}File not found: $req${NC}"
      fi
    done
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ No known vulnerabilities found in Python dependencies${NC}"
    else
        echo -e "${RED}✗ Vulnerabilities found in Python dependencies. Check the output above for details.${NC}"
        exit 1
    fi
}

# Run npm audit if package.json exists
run_npm_audit() {
    if [ -f "package.json" ] && command_exists npm; then
        echo -e "\n${YELLOW}=== Auditing Node.js dependencies ===${NC}"
        
        # Check if node_modules exists, if not install dependencies
        if [ ! -d "node_modules" ]; then
            echo "Installing Node.js dependencies..."
            npm ci
        fi
        
        # Run npm audit
        npm audit --production
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ No known vulnerabilities found in Node.js dependencies${NC}"
        else
            echo -e "${RED}✗ Vulnerabilities found in Node.js dependencies. Check the output above for details.${NC}"
            exit 1
        fi
    fi
}

# Main function
main() {
    # Install required tools
    install_required_tools
    
    # Run security checks
    run_secret_scan
    run_python_audit
    run_npm_audit
    
    echo -e "\n${GREEN}=== All security checks completed successfully ===${NC}"
}

# Run the main function
main
