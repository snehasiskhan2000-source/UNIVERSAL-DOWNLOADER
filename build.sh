#!/usr/bin/env bash
# Install Python packages
pip install -r requirements.txt

# Install Playwright browser and its system dependencies
playwright install chromium
playwright install-deps
