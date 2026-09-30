#!/bin/bash

# UBER MANUAL INVOICE CREATOR - Creates proper PDF files
# Usage: ./create_uber_manual.sh <year> <month> <amt1> <amt2> <amt3> <amt4> <amt5>
# Example: ./create_uber_manual.sh 2026 10 2956.85 1214.85 1456.00 1771.50 1840.50

if [ $# -lt 7 ]; then
    echo "Usage: $0 <year> <month> <amt1> <amt2> <amt3> <amt4> <amt5>"
    echo "Example: $0 2026 10 2956.85 1214.85 1456.00 1771.50 1840.50"
    exit 1
fi

YEAR=$1
MONTH=$2
AMT1=$3
AMT2=$4
AMT3=$5
AMT4=$6
AMT5=$7

# Get month name and short form
case $MONTH in
    1) MONTH_NAME="January"; MONTH_SHORT="jan";;
    2) MONTH_NAME="February"; MONTH_SHORT="feb";;
    3) MONTH_NAME="March"; MONTH_SHORT="mar";;
    4) MONTH_NAME="April"; MONTH_SHORT="apr";;
    5) MONTH_NAME="May"; MONTH_SHORT="may";;
    6) MONTH_NAME="June"; MONTH_SHORT="jun";;
    7) MONTH_NAME="July"; MONTH_SHORT="jul";;
    8) MONTH_NAME="August"; MONTH_SHORT="aug";;
    9) MONTH_NAME="September"; MONTH_SHORT="sep";;
    10) MONTH_NAME="October"; MONTH_SHORT="oct";;
    11) MONTH_NAME="November"; MONTH_SHORT="nov";;
    12) MONTH_NAME="December"; MONTH_SHORT="dec";;
esac

echo "=========================================="
echo "CREATING UBER MANUAL INVOICES"
echo "Month: $MONTH_NAME $YEAR"
echo "Amounts: $AMT1, $AMT2, $AMT3, $AMT4, $AMT5"
echo "=========================================="

# Create PDFs on VPS
ssh racknerd bash << ENDSSH
cd /home/harvad/invoice-processor/backend/invoices

# Function to create proper PDF
create_uber_pdf() {
    local filename=\$1
    local week=\$2
    local amount=\$3
    local month_name=\$4
    local year=\$5
    
    cat > "\$filename" << 'ENDPDF'
%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >>
/MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 180 >>
stream
BT
/F1 12 Tf
50 700 Td
(Uber Eats Payout - Manual Entry) Tj
0 -20 Td
(MONTH_NAME YEAR - Week WEEK) Tj
0 -20 Td
(Amount: AMOUNT SEK) Tj
0 -20 Td
(Ichiban Sushi) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000317 00000 n
trailer
<< /Size 5 /Root 1 0 R >>
startxref
547
%%EOF
ENDPDF
    
    # Replace placeholders
    sed -i "s/MONTH_NAME/\$month_name/g; s/YEAR/\$year/g; s/WEEK/\$week/g; s/AMOUNT/\$amount/g" "\$filename"
}

# Create 5 Uber manual PDFs with proper format
create_uber_pdf "ubereats_${MONTH_SHORT}${YEAR}_week1_${AMT1}_manual.pdf" "1" "$AMT1" "$MONTH_NAME" "$YEAR"
create_uber_pdf "ubereats_${MONTH_SHORT}${YEAR}_week2_${AMT2}_manual.pdf" "2" "$AMT2" "$MONTH_NAME" "$YEAR"
create_uber_pdf "ubereats_${MONTH_SHORT}${YEAR}_week3_${AMT3}_manual.pdf" "3" "$AMT3" "$MONTH_NAME" "$YEAR"
create_uber_pdf "ubereats_${MONTH_SHORT}${YEAR}_week4_${AMT4}_manual.pdf" "4" "$AMT4" "$MONTH_NAME" "$YEAR"
create_uber_pdf "ubereats_${MONTH_SHORT}${YEAR}_week5_${AMT5}_manual.pdf" "5" "$AMT5" "$MONTH_NAME" "$YEAR"

echo ""
echo "Files created:"
ls -lh ubereats_${MONTH_SHORT}${YEAR}_*.pdf
echo ""
echo "✅ Created 5 Uber manual invoices"
ENDSSH

echo ""
echo "=========================================="
echo "✅ UBER MANUAL INVOICES CREATED!"
echo "=========================================="
echo ""
echo "Files created on VPS:"
echo "  - ubereats_${MONTH_SHORT}${YEAR}_week1_${AMT1}_manual.pdf"
echo "  - ubereats_${MONTH_SHORT}${YEAR}_week2_${AMT2}_manual.pdf"
echo "  - ubereats_${MONTH_SHORT}${YEAR}_week3_${AMT3}_manual.pdf"
echo "  - ubereats_${MONTH_SHORT}${YEAR}_week4_${AMT4}_manual.pdf"
echo "  - ubereats_${MONTH_SHORT}${YEAR}_week5_${AMT5}_manual.pdf"
echo ""
echo "Now refresh: https://invoices.bluehawana.com"
echo "Uber should show 5/5 matched"
echo "=========================================="
