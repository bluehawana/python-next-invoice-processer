from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict
import os
import shutil
from stripe_module import download_stripe_payouts, generate_payout_reports, settings
from ocr_module import process_handwritten_image, reconcile_invoices
from email_module import fetch_email_invoices
from print_module import batch_print_invoices, print_pdf
from bankgiro_module import fetch_bankgiro_data, generate_bankgiro_report
from r2_module import upload_file_to_r2, generate_presigned_url
import asyncio

app = FastAPI()

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://invoices.bluehawana.com",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3005",
        "http://127.0.0.1:3005",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Static Files ---
os.makedirs(settings.INVOICE_STORAGE_PATH, exist_ok=True)
app.mount("/static/invoices", StaticFiles(directory=settings.INVOICE_STORAGE_PATH), name="invoices")

# --- Global State ---
handwritten_records = {}
reconciliation_results = []

# Persistent storage for handwritten data
HANDWRITTEN_DATA_FILE = "handwritten_data_persistent.json"

def _filter_month_files(files: list, year: int, month: int) -> list:
    """Return only invoices for the specified payment month.
    
    CRITICAL BUSINESS LOGIC - PAYMENT PERIOD RULES:
    ================================================
    Foodora & Uber have ~2 week payment delays:
    - Work done in last 2 weeks of PREVIOUS month gets paid in CURRENT month
    - Work done in first 2 weeks of CURRENT month gets paid in CURRENT month
    
    Example: August 2026 payment includes:
    - Invoices from Jul 16-31 (late July work)
    - Invoices from Aug 1-15 (early August work)
    
    Therefore: Always include invoices from BOTH months!
    """
    result = []
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    
    for f in files:
        name = os.path.basename(f).lower()
        
        # Manual invoices with month name (e.g., aug2026, sep2026)
        month_names = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        target_month_name = month_names[month - 1]
        if f"{target_month_name}{year}" in name:
            result.append(f)
            
        # Wolt: semi-monthly periods with dates in filename
        elif "wolt" in name:
            if f"{year}-{month:02d}" in name or f"{prev_year}-{prev_month:02d}-16__{year}-{month:02d}-01" in name:
                result.append(f)
                
        # Foodora: Include invoices from late previous month + current month
        # Approximate ID ranges (50 IDs per month, start ~100 IDs before current)
        elif "foodora" in name:
            import re
            m = re.search(r'foodora_(\d+)_', name)
            if m:
                # Rough estimate: 50 IDs per month, include previous 100 IDs
                base_id = 11000 + (year - 2025) * 600 + month * 50
                if int(m.group(1)) in range(base_id - 100, base_id + 100):
                    result.append(f)
                    
        # Uber: Include invoices from late previous month + current month
        elif "uber" in name:
            import re
            m = re.search(r'ubereats_(\d+)_', name)
            if m:
                # Rough estimate: 50 IDs per month, include previous 200 IDs
                base_id = 11000 + (year - 2025) * 600 + month * 50
                if int(m.group(1)) in range(base_id - 200, base_id + 100):
                    result.append(f)
                    
        # Stripe: match by payout ID prefix (changes monthly)
        # Jan 2026 = po_1N, Feb 2026 = po_1O, ..., Aug 2026 = po_1U, etc.
        elif "stripe_payout" in name:
            # Stripe IDs increment alphabetically starting from 1N for Jan 2026
            # Mapping: Jan=N, Feb=O, Mar=P, Apr=Q, May=R, Jun=S, Jul=T, Aug=U, Sep=V, Oct=W, Nov=X, Dec=Y
            months_since_jan_2026 = (year - 2026) * 12 + (month - 1)
            prefix_num = 1 + months_since_jan_2026 // 26
            # Start from 'N' for Jan 2026
            prefix_letter = chr(ord('N') + (months_since_jan_2026 % 26))
            import re
            m = re.search(rf'po_({prefix_num}{prefix_letter}\w+)\.pdf', name)
            if m:
                result.append(f)
                
    return result

def save_handwritten_data():
    """Save handwritten data to disk for persistence across restarts"""
    import json
    try:
        # Only save if there's actual data to prevent overwriting with empty dict
        if handwritten_records:
            with open(HANDWRITTEN_DATA_FILE, 'w') as f:
                json.dump(handwritten_records, f, indent=2)
            print(f"[PERSIST] Saved handwritten data: {len(handwritten_records)} partners")
        else:
            print(f"[PERSIST] Skipping save - no handwritten data to persist")
    except Exception as e:
        print(f"[PERSIST] Error saving handwritten data: {e}")

def load_handwritten_data():
    """Load handwritten data from disk"""
    global handwritten_records
    import json
    try:
        if os.path.exists(HANDWRITTEN_DATA_FILE):
            with open(HANDWRITTEN_DATA_FILE, 'r') as f:
                handwritten_records = json.load(f)
            print(f"[PERSIST] Loaded handwritten data: {len(handwritten_records)} partners")
            return True
    except Exception as e:
        print(f"[PERSIST] Error loading handwritten data: {e}")
    return False

@app.on_event("startup")
async def startup_auto_reconcile():
    """On startup, auto-reconcile using any PDFs already on disk so state survives restarts."""
    global reconciliation_results
    import glob
    import datetime
    
    # Load persisted handwritten data
    load_handwritten_data()

    # Use absolute path to avoid relative path issues with systemd
    invoice_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), settings.INVOICE_STORAGE_PATH))
    os.makedirs(invoice_dir, exist_ok=True)

    # Get all PDF files without month filtering - let reconciliation handle matching
    existing_files = glob.glob(os.path.join(invoice_dir, "*.pdf"))
    
    # Get invoices for August 2026 (includes late July per business rules)
    existing_files = _filter_month_files(glob.glob(os.path.join(invoice_dir, "*.pdf")), 2026, 8)
    
    print(f"[STARTUP] Invoice dir: {invoice_dir}")
    print(f"[STARTUP] Found {len(existing_files)} existing PDFs")
    print(f"[STARTUP] Loaded handwritten data for {len(handwritten_records)} partners")
    
    if existing_files and handwritten_records:
        try:
            # Try to get Stripe payouts for current display month (August 2026)
            st_payouts = download_stripe_payouts(2026, 8)
        except Exception:
            st_payouts = []
        reconciliation_results = reconcile_invoices(handwritten_records, st_payouts, existing_files)
        print(f"[STARTUP] Auto-reconcile complete: {len(reconciliation_results)} partners")
    else:
        print(f"[STARTUP] Skipping reconciliation: files={len(existing_files)}, handwritten={len(handwritten_records)}")

# --- Background Workflows ---
async def run_unified_workflow(year: int, month: int):
    global reconciliation_results
    print(f"--- Background Sync for {year}-{month:02d} ---")
    
    # 1. Collect
    st_payouts = download_stripe_payouts(year, month)
    email_files = fetch_email_invoices(year, month)
    
    payout_ids = [p['id'] for p in st_payouts]
    stripe_pdfs = []
    try:
        stripe_pdfs = await generate_payout_reports(payout_ids)
        print(f"Generated {len(stripe_pdfs)} Stripe PDF reports")
    except Exception as e:
        print(f"WARNING: Stripe PDF generation failed: {e}")
        print("Continuing with email invoices only...")
    
    # Inject manually-created PDFs from a persistent folder (never cleaned up)
    import glob
    manual_dir = os.path.join(os.path.dirname(os.path.abspath(settings.INVOICE_STORAGE_PATH)), "manual_invoices")
    os.makedirs(manual_dir, exist_ok=True)
    email_basenames = {os.path.basename(f) for f in email_files}
    for mf in glob.glob(os.path.join(manual_dir, "*.pdf")):
        if os.path.basename(mf) not in email_basenames:
            email_files.append(mf)
            print(f"Injected manual PDF: {os.path.basename(mf)}")
    
    all_files = email_files + stripe_pdfs

    # Also inject manual Aug 2026 PDFs (e.g. Uber manual invoices in invoices/)
    import re
    invoice_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), settings.INVOICE_STORAGE_PATH))
    for mf in glob.glob(os.path.join(invoice_dir, "*.pdf")):
        name = os.path.basename(mf).lower()
        if "aug2026" in name and mf not in all_files:
            all_files.append(mf)
            print(f"Injected Aug2026 manual PDF: {os.path.basename(mf)}")

    # 2. Reconcile using payment-period-aware file filter
    aug_files = _filter_month_files(all_files, year, month)
    reconciliation_results = reconcile_invoices(handwritten_records, st_payouts, aug_files)
    print(f"--- Sync Completed. {len(aug_files)} files for {year}-{month:02d} payment period. ---")

# --- Endpoints ---
@app.get("/")
def read_root():
    return {"status": "Invoice Processor API is running"}

from fastapi.responses import RedirectResponse

@app.get("/view-file")
def view_file(path: str):
    """
    Serves invoice files from the local VPS storage.
    Path should be just the filename (not full path).
    """
    # Extract just the filename
    filename = os.path.basename(path)
    # Serve from static mount
    return RedirectResponse(f"/static/invoices/{filename}")

@app.post("/upload-seb-transactions")
async def upload_seb_transactions(file: UploadFile = File(...), year: int = 2026, month: int = 1):
    """
    Upload SEB transaction export (CSV/Excel) to generate Bankgiro report.
    """
    global reconciliation_results
    
    # Read file content
    content = await file.read()
    
    # Parse SEB file
    from bankgiro_module import parse_seb_csv, generate_bankgiro_report
    bankgiro_data = parse_seb_csv(content, year, month)
    
    if not bankgiro_data:
        raise HTTPException(status_code=400, detail="No Bankgiro transactions found in file")
    
    # Generate report
    report_path = generate_bankgiro_report(bankgiro_data, year, month)
    
    if not report_path:
        raise HTTPException(status_code=400, detail="No transactions with >1 payment found")
    
    # Upload to R2 if configured
    r2_uri = upload_file_to_r2(report_path)
    
    return {
        "message": "Bankgiro report generated",
        "transactions_count": len(bankgiro_data),
        "report_file": r2_uri or report_path,
        "data": bankgiro_data
    }

@app.post("/upload-paper")
async def upload_paper(file: UploadFile = File(...)):
    global handwritten_records, reconciliation_results
    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    parsed_data = process_handwritten_image(file_path)
    if parsed_data:
        handwritten_records = parsed_data
        save_handwritten_data()  # Only persist if OCR actually found something
    reconciliation_results = reconcile_invoices(handwritten_records, [], [])
    
    return {"message": "OCR Complete. Recognition results loaded.", "results": reconciliation_results}

class ManualHandwrittenInput(BaseModel):
    """Manual input of handwritten amounts when OCR is not available."""
    records: Dict[str, List[float]]

@app.post("/upload-handwritten-manual")
async def upload_handwritten_manual(data: ManualHandwrittenInput):
    """
    Manually enter handwritten amounts when OCR/vision API is unavailable.
    Example body: {"records": {"Wolt": [3234.64, 1668.34], "Uber": [1017.25]}}
    """
    global handwritten_records, reconciliation_results
    
    # Normalise keys to handle "Uber Eats" → "Uber", "Hem" → "Stripe"
    normalised = {}
    for partner, amounts in data.records.items():
        p_lower = partner.lower().strip()
        if "wolt" in p_lower:
            normalised["Wolt"] = amounts
        elif "uber" in p_lower:
            normalised["Uber"] = amounts
        elif "foodora" in p_lower:
            normalised["Foodora"] = amounts
        elif "stripe" in p_lower or "hem" in p_lower:
            normalised["Stripe"] = amounts
        elif "swish" in p_lower:
            normalised["Swish"] = amounts
        else:
            normalised[partner] = amounts
    
    handwritten_records = normalised
    save_handwritten_data()  # Persist to disk
    
    # Scan for payment month files (includes late previous month per business rules)
    import glob, datetime
    invoice_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), settings.INVOICE_STORAGE_PATH))
    all_files = glob.glob(os.path.join(invoice_dir, "*.pdf"))
    existing_files = _filter_month_files(all_files, 2026, 8)
    
    # Get Stripe payouts for the display month (August 2026)
    try:
        from stripe_module import download_stripe_payouts
        st_payouts = download_stripe_payouts(2026, 8)
    except Exception:
        st_payouts = []
    
    # Debug: Count Stripe files
    stripe_files_count = len([f for f in existing_files if "stripe" in os.path.basename(f).lower()])
    print(f"[MANUAL-UPLOAD] Total files: {len(existing_files)}, Stripe: {stripe_files_count}")
    
    reconciliation_results = reconcile_invoices(handwritten_records, st_payouts, existing_files)
    
    return {
        "message": f"Manual records loaded: {len(normalised)} partners, found {len(existing_files)} PDFs",
        "records": normalised,
        "results": reconciliation_results
    }

@app.get("/reconciliation-status")
def get_reconciliation_status():
    return {
        "status": "success", 
        "records": reconciliation_results,
        "config": {
            "Stripe": bool(settings.STRIPE_API_KEY),
            "Foodora": bool(settings.EMAIL_USER),
            "UberEats": bool(settings.EMAIL_USER),
            "Wolt": bool(settings.EMAIL_USER),
            "Swish": True
        }
    }

@app.post("/print-file")
@app.post("/print-file")
def print_file_endpoint(file_path: str):
    # Handle R2 Remote Files
    temp_file = None
    if file_path.startswith("r2://"):
        from r2_module import get_r2_client
        s3 = get_r2_client()
        parts = file_path.replace("r2://", "").split("/", 1)
        if len(parts) == 2:
           bucket, key = parts
           temp_file = os.path.join(settings.INVOICE_STORAGE_PATH, key) # Re-download temporarily
           try:
               s3.download_file(bucket, key, temp_file)
               file_path = temp_file
           except Exception as e:
               raise HTTPException(status_code=500, detail=f"Failed to download from R2: {e}")

    # Handle Local Files
    if not os.path.exists(file_path):
        file_path = os.path.join(settings.INVOICE_STORAGE_PATH, os.path.basename(file_path))
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
    
    success = print_pdf(file_path)
    
    # Cleanup temp file
    if temp_file and os.path.exists(temp_file):
        os.remove(temp_file)
        
    if success:
        return {"message": "Printed"}
    raise HTTPException(status_code=500, detail="Print failed")

@app.post("/print-batch")
def print_batch_endpoint(file_paths: List[str]):
    batch_print_invoices(file_paths)
    return {"message": f"Printed {len(file_paths)} files"}

@app.post("/delete-all-invoices")
def delete_all_invoices():
    """Delete all invoice PDFs from VPS after printing."""
    deleted = []
    for f in os.listdir(settings.INVOICE_STORAGE_PATH):
        if f.endswith(".pdf"):
            path = os.path.join(settings.INVOICE_STORAGE_PATH, f)
            os.remove(path)
            deleted.append(f)
    return {"message": f"Deleted {len(deleted)} files", "files": deleted}

@app.post("/trigger-download")
async def trigger_download(background_tasks: BackgroundTasks, year: int = 2025, month: int = 12):
    background_tasks.add_task(run_unified_workflow, year, month)
    return {"message": "Sync started"}

@app.post("/generate-monthly-invoices")
async def generate_monthly_invoices(year: int, month: int):
    """
    Generate all invoices for a specific month (Stripe, Uber, Wolt, Foodora).
    Returns list of generated files.
    """
    print(f"Generating invoices for {year}-{month:02d}")
    
    # 1. Generate Stripe payouts
    st_payouts = download_stripe_payouts(year, month)
    payout_ids = [p['id'] for p in st_payouts]
    stripe_pdfs = []
    try:
        stripe_pdfs = await generate_payout_reports(payout_ids)
        print(f"✓ Generated {len(stripe_pdfs)} Stripe invoices")
    except Exception as e:
        print(f"✗ Stripe generation failed: {e}")
    
    # 2. Fetch email invoices (Uber, Wolt, Foodora)
    email_files = fetch_email_invoices(year, month)
    print(f"✓ Generated {len(email_files)} email invoices")
    
    all_files = stripe_pdfs + email_files
    
    # Return relative paths for frontend
    relative_paths = [os.path.basename(f) for f in all_files]
    
    return {
        "message": f"Generated {len(all_files)} invoices",
        "year": year,
        "month": month,
        "files": relative_paths,
        "stripe_count": len(stripe_pdfs),
        "email_count": len(email_files)
    }

from fastapi.responses import FileResponse
import zipfile
import tempfile

@app.get("/download-monthly-zip")
async def download_monthly_zip(year: int, month: int):
    """
    Download all invoices for a specific month as a ZIP file.
    """
    # Create temp zip file
    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    
    with zipfile.ZipFile(temp_zip.name, 'w') as zipf:
        # Add all PDFs from the invoice storage
        for filename in os.listdir(settings.INVOICE_STORAGE_PATH):
            if filename.endswith('.pdf'):
                file_path = os.path.join(settings.INVOICE_STORAGE_PATH, filename)
                zipf.write(file_path, filename)
    
    return FileResponse(
        temp_zip.name,
        media_type='application/zip',
        filename=f'invoices_{year}_{month:02d}.zip'
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
