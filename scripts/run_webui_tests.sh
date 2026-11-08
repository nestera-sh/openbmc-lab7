#!/bin/bash
echo "Running WebUI Tests..."
mkdir -p reports/webui

cd tests/webui

python3 -m pytest test_all.py -v --junitxml=../../reports/webui/junit.xml || true
cd ../..