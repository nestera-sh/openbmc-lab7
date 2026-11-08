#!/bin/bash
echo "Running Redfish API Tests..."
mkdir -p reports/api

cd tests/api
python3 -m pytest test_redfish.py -v --junitxml=../../reports/api/junit.xml || true
cd ../..