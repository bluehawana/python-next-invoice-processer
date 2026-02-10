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
        "http://localhost:3005",
        "http://127.0.0.1:3005",
        "http://localhost:3000",
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

# --- Background Workflows ---
async def run_unified_workflow(year: int, month: int):
    global reconciliation_results
    print(f"--- Background Sync for {year}-{month:02d} ---")
    
    # 1. Collect
    st_payouts = download_stripe_payouts(year, month)
    email_files = fetch_email_invoices(year, month)
    
    payout_ids = [p['id'] for p in st_payouts]
    stripe_pdfs = await generate_payout_reports(payout_ids)
    
    # Bankgiro Processing (Disabled for now)
    # bankgiro_data = fetch_bankgiro_data(year, month)
    # bg_report = generate_bankgiro_report(bankgiro_data)
    
    all_files = email_files + stripe_pdfs
    # if bg_report:
    #     all_files.append(bg_report)
         
    # 2. Upload to R2 (if configured) & Cleanup
    r2_files = []
    for fpath in all_files:
        if os.path.exists(fpath):
            # Upload (deletes local file on success)
            r2_uri = upload_file_to_r2(fpath)
            r2_files.append(r2_uri)
    
    # 3. Reconcile using R2 URIs
    reconciliation_results = reconcile_invoices(handwritten_records, st_payouts, r2_files)
    print(f"--- Sync Completed. Processed {len(r2_files)} files. ---")

# --- Endpoints ---
@app.get("/")
def read_root():
    return {"status": "Invoice Processor API is running"}

from fastapi.responses import RedirectResponse

@app.get("/view-file")
def view_file(path: str):
    """
    Redirects to the file content.
    - If R2: Generates a pre-signed URL and redirects.
    - If Local: Redirects to the static file server path.
    """
    if path.startswith("r2://"):
        from r2_module import generate_presigned_url
        url = generate_presigned_url(path)
        if url:
             return RedirectResponse(url)
        else:
             raise HTTPException(status_code=404, detail="Could not generate R2 URL")
    
    # Local File
    filename = os.path.basename(path)
    # Ensure we only serve from the invoices dir for security
    return RedirectResponse(f"/static/invoices/{filename}")

@app.post("/upload-paper")
async def upload_paper(file: UploadFile = File(...)):
    global handwritten_records, reconciliation_results
    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    parsed_data = process_handwritten_image(file_path)
    handwritten_records = parsed_data
    reconciliation_results = reconcile_invoices(handwritten_records, [], [])
    
    return {"message": "OCR Complete. Recognition results loaded.", "results": reconciliation_results}

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

@app.post("/trigger-download")
async def trigger_download(background_tasks: BackgroundTasks, year: int = 2025, month: int = 12):
    background_tasks.add_task(run_unified_workflow, year, month)
    return {"message": "Sync started"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
