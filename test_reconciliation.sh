#!/bin/bash

echo "Testing Invoice Reconciliation Workflow"
echo "========================================"
echo ""

API_URL="https://api.bluehawana.com"

echo "1. Checking API status..."
curl -s "$API_URL/" | jq .
echo ""

echo "2. Getting current reconciliation status..."
curl -s "$API_URL/reconciliation-status" | jq '.records[] | {partner, handwritten_count, matched_count, file_count: (.files | length)}'
echo ""

echo "3. Triggering sync for January 2026..."
curl -s -X POST "$API_URL/trigger-download?year=2026&month=1" | jq .
echo ""

echo "Waiting 60 seconds for sync to complete..."
for i in {1..12}; do
    echo -n "."
    sleep 5
done
echo ""
echo ""

echo "4. Checking reconciliation status after sync..."
curl -s "$API_URL/reconciliation-status" | jq '.records[] | {partner, handwritten_count, matched_count, reconciled, file_count: (.files | length)}'
echo ""

echo "Done!"
