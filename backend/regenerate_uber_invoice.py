"""
Regenerate the last Uber invoice with correct amount: 113.1 kr
"""
from fpdf import FPDF
from stripe_module import settings
import os

def generate_uber_invoice_fixed():
    """Generate the corrected Uber invoice."""
    
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
    pdf.cell(0, 8, "Betalningsöversikt över 01/06/2026 - 01/12/2026", ln=True)
    pdf.ln(3)
    
    # Greeting
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, "Hej Ichiban Sushi,", ln=True)
    pdf.ln(2)
    pdf.multi_cell(0, 5, "Vi hoppas att du har en bra vecka. Nedan hittar du din veckovisa betalningsöversikt. Fakturan för ovan nämnda period finns redan tillgänglig i Uber Eats Manager.")
    pdf.ln(2)
    pdf.cell(0, 5, "Tack för att du är en partner,", ln=True)
    pdf.cell(0, 5, "Uber Eats-teamet", ln=True)
    pdf.ln(8)
    
    # === Total försäljning section ===
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Total försäljning", ln=True)
    pdf.ln(3)
    
    total_amount = "113,10"
    num_orders = "1"
    
    # Draw boxes for Beställningar and Total Betalning
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
    pdf.cell(90, 12, num_orders, align='C')
    
    # Box 2: Total Betalning
    pdf.rect(105, y_start, 95, 30)
    pdf.set_xy(105, y_start + 3)
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(95, 5, "Total Betalning", align='C', ln=True)
    pdf.set_xy(105, y_start + 12)
    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(6, 149, 55)  # Uber green
    pdf.cell(95, 12, f"{total_amount} kr", align='C')
    
    pdf.set_y(y_start + 38)
    
    # === Betalningsberäkning section ===
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Betalningsberäkning", ln=True)
    pdf.ln(3)
    
    # Table header
    pdf.set_font("Arial", "B", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(60, 6, "DAG/UPPHÄMTNINGSTID", ln=False)
    pdf.cell(40, 6, "Beställningar", align='C', ln=False)
    pdf.cell(0, 6, "FÖRSÄLJNING (EFTER SKATT)", align='R', ln=True)
    pdf.ln(2)
    
    # Daily data
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(60, 6, "01/10/2026", ln=False)
    pdf.cell(40, 6, "1", align='C', ln=False)
    pdf.cell(0, 6, "159,00 kr", align='R', ln=True)
    
    pdf.ln(3)
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
    
    add_summary_line("Totalbelopp", "159,00 kr")
    add_summary_line("Uber Eats-avgift", "-38,16 kr")
    add_summary_line("Moms på Uber Eats-avgift", "-7,63 kr")
    add_summary_line("Nettoförsäljning", "113,21 kr")
    
    pdf.ln(5)
    
    # Final Total Betalning in green
    pdf.set_font("Arial", "B", 12)
    pdf.cell(100, 10, "", ln=False)
    pdf.set_text_color(6, 149, 55)
    pdf.cell(50, 10, "Total Betalning", ln=False)
    pdf.cell(0, 10, f"{total_amount} kr", align='R', ln=True)
    
    # Save the file
    os.makedirs(settings.INVOICE_STORAGE_PATH, exist_ok=True)
    filepath = os.path.join(settings.INVOICE_STORAGE_PATH, "ubereats_10935_email_body.pdf")
    pdf.output(filepath)
    print(f"✓ Regenerated Uber invoice: {filepath}")
    print(f"  Total Betalning: {total_amount} kr")
    return filepath

if __name__ == "__main__":
    generate_uber_invoice_fixed()
