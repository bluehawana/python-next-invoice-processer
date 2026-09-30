#!/bin/bash

# UBER MANUAL INVOICE CREATOR
# Usage: ./create_uber_manual.sh <year> <month> <amt1> <amt2> <amt3> <amt4> <amt5>
# Example: ./create_uber_manual.sh 2026 10 2956.85 1214.85 1456.00 1771.50 1840.50

if [ $# -lt 7 ]; then
    echo "Usage: $0 <year> <month> <amt1> <amt2> <amt3> <amt4> <amt5>"
    echo "Example: $0 2026 10 2956.85 1214.85 1456.00 1771.50 1840.50"
    exit 1
fi

YEAR=$1
MONTH=$2
MONTH_NAME=$(date -j -f "%m" "$MONTH" "+%B" 2>/dev/null || echo "Month$MONTH")
AMT1=$3
AMT2=$4
AMT3=$5
AMT4=$6
AMT5=$7

echo "=========================================="
echo "CREATING UBER MANUAL INVOICES"
echo "Month: $MONTH_NAME $YEAR"
echo "Amounts: $AMT1, $AMT2, $AMT3, $AMT4, $AMT5"
echo "=========================================="

ssh racknerd << ENDSSH
cd /home/harvad/invoice-processor/backend/invoices

# Create 5 Uber manual PDFs
echo "Uber Week 1: $AMT1 SEK
Period: Week 1 of $MONTH_NAME $YEAR
Restaurant: Ichiban Sushi
Manual Invoice" > ubereats_${YEAR}_${MONTH}_week1_${AMT1}_manual.pdf

echo "Uber Week 2: $AMT2 SEK
Period: Week 2 of $MONTH_NAME $YEAR
Restaurant: Ichiban Sushi
Manual Invoice" > ubereats_${YEAR}_${MONTH}_week2_${AMT2}_manual.pdf

echo "Uber Week 3: $AMT3 SEK
Period: Week 3 of $MONTH_NAME $YEAR
Restaurant: Ichiban Sushi
Manual Invoice" > ubereats_${YEAR}_${MONTH}_week3_${AMT3}_manual.pdf

echo "Uber Week 4: $AMT4 SEK
Period: Week 4 of $MONTH_NAME $YEAR
Restaurant: Ichiban Sushi
Manual Invoice" > ubereats_${YEAR}_${MONTH}_week4_${AMT4}_manual.pdf

echo "Uber Week 5: $AMT5 SEK
Period: Week 5 of $MONTH_NAME $YEAR
Restaurant: Ichiban Sushi
Manual Invoice" > ubereats_${YEAR}_${MONTH}_week5_${AMT5}_manual.pdf

ls -lh ubereats_${YEAR}_${MONTH}_*.pdf

echo ""
echo "✅ Created 5 Uber manual invoices"
ENDSSH

echo ""
echo "=========================================="
echo "✅ UBER MANUAL INVOICES CREATED!"
echo "=========================================="
echo ""
echo "Now refresh: https://invoices.bluehawana.com"
echo "Uber should show 5/5 matched"
echo "=========================================="
