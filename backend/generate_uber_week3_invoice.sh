#!/bin/bash
# Generate the missing Uber Eats invoice for week 3 (2253 kr)

cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Run the invoice generation script
python3 create_uber_2253_invoice.py

echo ""
echo "Invoice generated! Check ./invoices/ directory"
ls -lh ./invoices/ubereats_2253*
