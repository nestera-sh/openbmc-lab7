#!/bin/bash
echo "Running Locust Load Tests..."
mkdir -p reports/load

cd tests/load
locust -f locustfile.py --headless -u 10 -r 2 -t 30s --html ../../reports/load/report.html --csv ../../reports/load/stats || true
cd ../..