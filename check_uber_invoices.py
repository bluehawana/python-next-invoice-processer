#!/usr/bin/env python3
"""
Check Uber invoice amounts by extracting from text content
"""
import os
import re

def extract_amount_from_file(filepath):
    """Extract amount from Uber invoice file by reading text."""
    try:
        # Read file content
        with open(filepath, 'rb') as f:
            content = f.read().decode('utf-8', errors='ignore')
        
        # Look for Uber amount patterns
        patterns = [
            r'Total\s+Betalning\s+([\d.,]+)\s*kr',
            r'Total\s+Payment\s+([\d.,]+)\s*kr',
            r'Nettoförsäljning\s+([\d.,]+)\s*kr',
            r'([\d.,]+)\s*kr\s*\(SEK\)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                amount_str = match.group(1)
                # Clean the amount
                amount_str = amount_str.replace('.', '').replace(',', '.')
                try:
                    return float(amount_str)
                except ValueError:
                    pass
        
        # Also check filename for amount patterns
        filename = os.path.basename(filepath)
        amount_pattern = r'(\d+\.\d+|\d+,\d+)'
        matches = re.findall(amount_pattern, filename)
        for match in matches:
            try:
                amount_str = match.replace(',', '.')
                return float(amount_str)
            except ValueError:
                pass
        
        return 0
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return 0

def main():
    print("Checking Uber invoices...")
    print("Missing amounts: 228.80, 667.55, 677.55\n")
    
    # Find all Uber invoice files
    uber_files = []
    for root, dirs, files in os.walk("/Users/harvad/Projects/python-next-invoice-processer/backend"):
        for file in files:
            if 'uber' in file.lower() and file.endswith('.pdf'):
                uber_files.append(os.path.join(root, file))
    
    print(f"Found {len(uber_files)} Uber invoice files:")
    
    total_amount = 0
    found_amounts = []
    
    for filepath in uber_files:
        filename = os.path.basename(filepath)
        amount = extract_amount_from_file(filepath)
        
        if amount > 0:
            print(f"  {filename}: {amount:.2f} SEK")
            total_amount += amount
            found_amounts.append(amount)
        else:
            print(f"  {filename}: Could not extract amount")
    
    print(f"\nTotal Uber amount found: {total_amount:.2f} SEK")
    print(f"Amounts found: {', '.join(f'{a:.2f}' for a in found_amounts)}")
    
    # Check for missing amounts
    missing = [228.80, 667.55, 677.55]
    print("\nChecking for missing amounts:")
    
    for target in missing:
        found = False
        for amount in found_amounts:
            if abs(amount - target) < 0.5:  # 0.5 SEK tolerance
                print(f"  ✓ {target:.2f} found as {amount:.2f}")
                found = True
                break
        
        if not found:
            print(f"  ✗ {target:.2f} NOT FOUND")
    
    print("\nPossible issues:")
    print("1. Emails not downloaded from Gmail")
    print("2. Email filtering skipping some periods")
    print("3. PDF generation failing for some emails")
    print("4. Different email format for these amounts")

if __name__ == "__main__":
    main()