#!/usr/bin/env python3
"""
Create missing Uber Eats invoices for August 2026
Amounts from handwritten records and Uber dashboard
"""
from fpdf import FPDF
import os

def create_uber_invoice(amount: float, week_num: int, start_date: str, end_date: str, orders: int = 0) -> str:
    """Create Uber Eats invoice PDF"""
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
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
    
    # Date range
    pdf.set_font("Arial", "", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, f"Betalningsöversikt över {start_date} - {end_date}", ln=True)
    pdf.ln(3)
    
    # Greeting
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, "Hej Ichiban Sushi,", ln=True)
    pdf.ln(2)
    pdf.multi_cell(0, 5, "Vi hoppas att du har en bra vecka. Nedan hittar du din veckovisa betalningsöversikt.")
    pdf.ln(2)
    pdf.cell(0, 5, "Tack för att du är en partner,", ln=True)
    pdf.cell(0, 5, "Uber Eats-teamet", ln=True)
    pdf.ln(8)
    
    # === Total försäljning section ===
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Total försäljning", ln=True)
    pdf.ln(3)
    
    # Draw boxes
    y_start = pdf.get_y()
    
    # Box 1: Beställningar
    pdf.set_draw_color(200, 200, 200)
    pdf.rect(10, y_start, 90, 30)
    pdf.set_xy(10, y_start + 3)
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(90, 5, "Beställningar", align='C', ln=True)
    pdf.set_xy(10, y_start + 12)
    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(90, 12, str(orders) if orders > 0 else "-", align='C')
    
    # Box 2: Total Betalning
    pdf.rect(105, y_start, 95, 30)
    pdf.set_xy(105, y_start + 3)
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(95, 5, "Total Betalning", align='C', ln=True)
    pdf.set_xy(105, y_start + 12)
    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(6, 149, 55)  # Uber green
    
    # Format amount with Swedish notation
    amount_str = f"{amount:,.2f}".replace(",", " ").replace(".", ",")
    pdf.cell(95, 12, f"{amount_str} kr", align='C')
    
    pdf.set_y(y_start + 38)
    
    # === Betalningsberäkning section ===
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Betalningsberäkning", ln=True)
    pdf.ln(3)
    
    # Period info
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, f"Period: {start_date} till {end_date}", ln=True)
    pdf.cell(0, 6, f"Vecka {week_num} - Augusti 2026", ln=True)
    pdf.ln(5)
    
    pdf.set_draw_color(220, 220, 220)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    
    # Summary
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 9)
    pdf.cell(100, 6, "", ln=False)
    pdf.cell(50, 6, "Nettobetalning", ln=False)
    pdf.cell(0, 6, f"{amount_str} kr", align='R', ln=True)
    
    pdf.ln(5)
    
    # Final Total Betalning in green
    pdf.set_font("Arial", "B", 12)
    pdf.cell(100, 10, "", ln=False)
    pdf.set_text_color(6, 149, 55)
    pdf.cell(50, 10, "Total Betalning", ln=False)
    pdf.cell(0, 10, f"{amount_str} kr", align='R', ln=True)
    
    # Footer note
    pdf.ln(8)
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.multi_cell(0, 4, f"Notering: Denna faktura skapades manuellt fran handskriven dokumentation eftersom ingen e-postbekraftelse mottogs for denna utbetalning. Vecka {week_num}, Augusti 2026.".encode('latin-1', 'replace').decode('latin-1'))
    
    # Save
    output_dir = "./invoices"
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"ubereats_aug2026_week{week_num}_{amount:.2f}_manual.pdf"
    filepath = os.path.join(output_dir, filename)
    
    pdf.output(filepath)
    return filepath

if __name__ == "__main__":
    print("="*80)
    print("CREATING MISSING UBER EATS INVOICES - AUGUST 2026")
    print("="*80)
    
    # Week estimates based on typical Uber weekly cycles
    invoices = [
        {"amount": 677.95, "week": 1, "start": "2026-08-03", "end": "2026-08-09", "orders": 0},
        {"amount": 3075.15, "week": 2, "start": "2026-08-10", "end": "2026-08-16", "orders": 0},
        {"amount": 2904.20, "week": 3, "start": "2026-08-17", "end": "2026-08-23", "orders": 0},
    ]
    
    created = []
    for inv in invoices:
        print(f"\nCreating invoice for week {inv['week']}...")
        print(f"  Amount: {inv['amount']:,.2f} kr")
        print(f"  Period: {inv['start']} to {inv['end']}")
        
        filepath = create_uber_invoice(
            amount=inv['amount'],
            week_num=inv['week'],
            start_date=inv['start'],
            end_date=inv['end'],
            orders=inv['orders']
        )
        
        created.append(filepath)
        print(f"  ✅ Created: {os.path.basename(filepath)}")
    
    print("\n" + "="*80)
    print(f"✅ SUCCESS: Created {len(created)} Uber Eats invoices")
    print("="*80)
    
    total = sum(inv['amount'] for inv in invoices)
    print(f"\nTotal: {total:,.2f} kr")
    print("\nInvoices saved to: ./invoices/")
    
    for filepath in created:
        size = os.path.getsize(filepath)
        print(f"  - {os.path.basename(filepath)} ({size:,} bytes)")
