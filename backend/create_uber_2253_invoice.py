#!/usr/bin/env python3
"""
Create the missing Uber Eats invoice for 2253 kr (2026-07-13 to 2026-07-19)
Data from Uber Eats UI dashboard
"""
from fpdf import FPDF
import os

def create_uber_invoice_2253():
    """Create Uber Eats invoice for the missing 2253 kr payout."""
    
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
    pdf.cell(0, 8, "Betalningsöversikt över 13/07/26 - 19/07/26", ln=True)
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
    
    # Draw boxes for Beställningar and Total Betalning
    y_start = pdf.get_y()
    
    # Box 1: Beställningar (Orders)
    pdf.set_draw_color(200, 200, 200)
    pdf.rect(10, y_start, 90, 30)
    pdf.set_xy(10, y_start + 3)
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(90, 5, "Beställningar", align='C', ln=True)
    pdf.set_xy(10, y_start + 12)
    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(90, 12, "10", align='C')
    
    # Box 2: Total Betalning
    pdf.rect(105, y_start, 95, 30)
    pdf.set_xy(105, y_start + 3)
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(95, 5, "Total Betalning", align='C', ln=True)
    pdf.set_xy(105, y_start + 12)
    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(6, 149, 55)  # Uber green
    pdf.cell(95, 12, "2.253,00 kr", align='C')
    
    pdf.set_y(y_start + 38)
    
    # === Betalningsberäkning section ===
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Betalningsberäkning", ln=True)
    pdf.ln(3)
    
    # Period info
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, "Period: 2026-07-13 till 2026-07-19", ln=True)
    pdf.cell(0, 6, "Kunder: 9 | Betalda beställningar: 10", ln=True)
    pdf.cell(0, 6, "Transaktions-ID: F87HHHRZJ5H82QX", ln=True)
    pdf.cell(0, 6, "Nästa utbetalningsdatum: Aug 16, 2026", ln=True)
    pdf.ln(5)
    
    pdf.set_draw_color(220, 220, 220)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    
    # Summary lines
    def add_summary_line(label, value, bold=False):
        if bold:
            pdf.set_font("Arial", "B", 10)
        else:
            pdf.set_font("Arial", "", 9)
        pdf.cell(100, 6, "", ln=False)
        pdf.cell(50, 6, label, ln=False)
        pdf.cell(0, 6, value, align='R', ln=True)
    
    pdf.set_text_color(0, 0, 0)
    add_summary_line("Intäkter", "3.324,00 kr")
    add_summary_line("Uber-avgifter", "-1.071,00 kr")
    add_summary_line("Nettojusteringar vid beställningsfel", "0,00 kr")
    
    pdf.ln(5)
    
    # Final Total Betalning in green
    pdf.set_font("Arial", "B", 12)
    pdf.cell(100, 10, "", ln=False)
    pdf.set_text_color(6, 149, 55)
    pdf.cell(50, 10, "Total Betalning", ln=False)
    pdf.cell(0, 10, "2.253,00 kr", align='R', ln=True)
    
    # Footer note
    pdf.ln(8)
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.multi_cell(0, 4, "Notering: Denna faktura skapades manuellt från Uber Eats dashboard-data eftersom ingen e-postbekräftelse mottogs för denna utbetalning.")
    
    # Save the PDF
    output_dir = "./invoices"
    os.makedirs(output_dir, exist_ok=True)
    filename = "ubereats_2253.00_20260713-20260719_manual.pdf"
    filepath = os.path.join(output_dir, filename)
    
    pdf.output(filepath)
    return filepath

if __name__ == "__main__":
    print("Creating Uber Eats invoice for 2253 kr (2026-07-13 to 2026-07-19)...")
    filepath = create_uber_invoice_2253()
    print(f"✅ Invoice created: {filepath}")
    
    # Verify file size
    import os
    size = os.path.getsize(filepath)
    print(f"   File size: {size:,} bytes")
