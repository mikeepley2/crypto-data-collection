#!/bin/bash
# Check collectors via Kubernetes logs (no database queries)

echo "=================================================================================="
echo "COLLECTORS STATUS - VIA KUBERNETES LOGS"
echo "=================================================================================="
echo

echo "1️⃣  ONCHAIN COLLECTOR"
echo "--------------------------------------------------------------------------------"
kubectl logs -n crypto-data-collection -l app=onchain-collector --tail=30 2>/dev/null | grep -i "starting\|error\|collected\|finished" | tail -5
echo

echo "2️⃣  MACRO COLLECTOR"
echo "--------------------------------------------------------------------------------"
kubectl logs -n crypto-data-collection -l app=macro-collector --tail=30 2>/dev/null | grep -i "starting\|error\|collected\|finished\|fred" | tail -5
echo

echo "3️⃣  TECHNICAL CALCULATOR"
echo "--------------------------------------------------------------------------------"
kubectl logs -n crypto-data-collection -l app=technical-calculator --tail=30 2>/dev/null | grep -i "starting\|error\|calculated\|finished\|symbols" | tail -5
echo

echo "4️⃣  MATERIALIZED UPDATER"
echo "--------------------------------------------------------------------------------"
kubectl logs -n crypto-data-collection -l app=materialized-updater --tail=30 2>/dev/null | grep -i "starting\|finished\|processed\|error" | tail -5
echo

echo "=================================================================================="


