#!/usr/bin/env python3
"""
UBER MANUAL INVOICE CREATOR - Creates proper PyFPDF-formatted PDFs
Usage: ./create_uber_manual.py <year> <month> <amt1> <amt2> <amt3> <amt4> <amt5>
Example: ./create_uber_manual.py 2026 10 2956.85 1214.85 1456.00 1771.50 1840.50
"""

import sys
import subprocess
from datetime import datetime

if len(sys.argv) < 8:
    print("Usage: ./create_uber_manual.py <year> <month> <amt1> <amt2> <amt3> <amt4> <amt5>")
    print("Example: ./create_uber_manual.py 2026 10 2956.85 1214.85 1456.00 1771.50 1840.50")
    sys.exit(1)

year = int(sys.argv[1])
month = int(sys.argv[2])
amounts = [sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7]]

month_names = {
    1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
    7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"
}
month_short = {
    1: "jan", 2: "feb", 3: "mar", 4: "apr", 5: "may", 6: "jun",
    7: "jul", 8: "aug", 9: "sep", 10: "oct", 11: "nov", 12: "dec"
}

month_name = month_names[month]
month_abbr = month_short[month]

print("=" * 50)
print("CREATING UBER MANUAL INVOICES")
print(f"Month: {month_name} {year}")
print(f"Amounts: {', '.join(amounts)}")
print("=" * 50)

# Create Python script to run on VPS
python_code = f'''
import sys
sys.path.append("/home/harvad/invoice-processor/backend")
from fpdf import FPDF

def create_uber_pdf(filename, week, amount, year, month_name):
    pdf = FPDF()
    pdf.add_page()
    
    # Header: UBER EATS
    pdf.set_font("Arial", "B", 18)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(30, 10, "UBER", ln=False)
    pdf.set_font("Arial", "", 18)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, "EATS", ln=True)
    pdf.ln(8)
    
    # Restaurant name
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Ichiban Sushi", ln=True)
    
    # Date info
    pdf.set_font("Arial", "", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, f"Betalningsoversikt - {{month_name}} {{year}} Week {{week}}", ln=True)
    pdf.ln(3)
    
    # Greeting
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, "Hej Ichiban Sushi,", ln=True)
    pdf.ln(2)
    pdf.multi_cell(0, 5, "Vi hoppas att du har en bra vecka. Nedan hittar du din veckovisa betalningsoversikt.")
    pdf.ln(2)
    pdf.cell(0, 5, "Tack for att du ar en partner,", ln=True)
    pdf.cell(0, 5, "Uber Eats-teamet", ln=True)
    pdf.ln(8)
    
    # Total section
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Total forsaljning", ln=True)
    pdf.ln(3)
    
    # Amount details
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(100, 6, "Total Betalning", ln=False)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, f"{{amount}} kr", ln=True, align="R")
    
    pdf.set_font("Arial", "", 10)
    pdf.cell(100, 6, "Nettobetalning", ln=False)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, f"{{amount}} kr", ln=True, align="R")
    
    pdf.output(filename)
    print(f"Created: {{filename}}")

import os
os.chdir("/home/harvad/invoice-processor/backend/invoices")

# Create 5 PDFs
'''

for i, amt in enumerate(amounts, 1):
    week = i
    filename = f"ubereats_{month_abbr}{year}_week{week}_{amt}_manual.pdf"
    python_code += f'create_uber_pdf("{filename}", {week}, "{amt}", {year}, "{month_name}")\n'

# Write Python code to temp file and execute on VPS
with open('/tmp/create_uber_temp.py', 'w') as f:
    f.write(python_code)

# Upload and execute
print("\nUploading script to VPS...")
subprocess.run(['scp', '/tmp/create_uber_temp.py', 'racknerd:/tmp/'])

print("Creating PDFs on VPS...")
result = subprocess.run(['ssh', 'racknerd', 
                        'cd /home/harvad/invoice-processor/backend && source venv/bin/activate && python3 /tmp/create_uber_temp.py'], 
                       capture_output=True, text=True, shell=False)
print(result.stdout)
if result.stderr:
    print("Errors:", result.stderr)

# List created files
print("\nVerifying files...")
subprocess.run(['ssh', 'racknerd', f'ls -lh /home/harvad/invoice-processor/backend/invoices/ubereats_{month_abbr}{year}_*.pdf'])

print("\n" + "=" * 50)
print("✅ UBER MANUAL INVOICES CREATED!")
print("=" * 50)
print(f"\nFiles created:")
for i, amt in enumerate(amounts, 1):
    print(f"  - ubereats_{month_abbr}{year}_week{i}_{amt}_manual.pdf")
print("\nNow refresh: https://invoices.bluehawana.com")
print("Uber should show 5/5 matched")
print("=" * 50)
