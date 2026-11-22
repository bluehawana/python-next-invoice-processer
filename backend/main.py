from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import shutil
from stripe_module import download_stripe_payouts, generate_payout_reports, settings
from ocr_module import (process_handwritten_image, reconcile_invoices, normalise_handwritten,
                        extract_text_from_pdf, is_uber_statement)
from email_module import fetch_email_invoices, payment_window, load_received_index
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
current_period = {"year": 0, "month": 0}   # the payment month the dashboard is working on
sync_state = {"running": False, "message": ""}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Legacy single-file storage (pre per-month storage). Only read once, for migration.
HANDWRITTEN_DATA_FILE = os.path.join(BASE_DIR, "handwritten_data_persistent.json")
HANDWRITTEN_DIR = os.path.join(BASE_DIR, "handwritten_data")
PERIOD_STATE_FILE = os.path.join(HANDWRITTEN_DIR, "current_period.json")
MONTH_NAMES = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']


def default_period() -> tuple:
    """Invoices are collected for the PREVIOUS calendar month."""
    import datetime
    first = datetime.date.today().replace(day=1)
    prev = first - datetime.timedelta(days=1)
    return prev.year, prev.month


def _valid_period(year: Optional[int], month: Optional[int]) -> bool:
    return bool(year and month and 2020 <= year <= 2100 and 1 <= month <= 12)

def _filter_month_files(files: list, year: int, month: int) -> list:
    """Return only invoices for the specified payment month.

    CRITICAL BUSINESS LOGIC - PAYMENT PERIOD RULES:
    ================================================
    Wolt, Foodora & Uber have ~2 week payment delays:
    - Work done in last 2 weeks of PREVIOUS month gets paid in CURRENT month
    - Work done in first 2 weeks of CURRENT month gets paid in CURRENT month

    Example: October payment includes invoices from Sep 15-30 AND from October.
    Therefore: Always include invoices from BOTH months!

    How a file is placed in a month, in order of reliability:
    1. The date its email was received (recorded by the email fetch) - inside the payment window.
    2. Dates / month names in the file name.
    3. Legacy fallback: the email sequence number in the file name (rough estimate).
    """
    import re, datetime
    result = []
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    window_start, window_end = payment_window(year, month)
    received_index = load_received_index()
    month_tag = f"{MONTH_NAMES[month - 1]}{year}"
    prev_tag = f"{MONTH_NAMES[prev_month - 1]}{prev_year}"

    def in_window(date_str: str) -> bool:
        try:
            return window_start <= datetime.date.fromisoformat(date_str) < window_end
        except Exception:
            return False

    for f in files:
        base = os.path.basename(f)
        name = base.lower()
        keep = False

        # Stripe: every payout PDF is kept; matching is done against the month's payouts from the API
        if "stripe_payout" in name:
            keep = True

        # 1. Received date known -> the payment window decides
        elif base in received_index:
            keep = in_window(received_index[base])

        # 2a. Manual invoices named with a month (e.g. ubereats_oct2026_week3_...):
        elif month_tag in name:
            keep = True

        # 2b. Wolt: semi-monthly period dates in the file name
        elif "wolt" in name:
            periods = re.findall(r'(\d{4}-\d{2}-\d{2})__(\d{4}-\d{2}-\d{2})', name)
            if periods:
                # the report is issued when the period ends -> period end date inside the payment window,
                # and the period itself not older than the last two weeks of the previous month
                start_s, end_s = periods[-1]
                try:
                    p_start = datetime.date.fromisoformat(start_s)
                    p_end = datetime.date.fromisoformat(end_s)
                    keep = p_start >= window_start and p_end < window_end
                except Exception:
                    keep = False
            else:
                keep = f"{year}-{month:02d}" in name

        # 3. Legacy Foodora / Uber files: estimate from the email sequence number
        elif "foodora" in name:
            m = re.search(r'foodora_(\d+)_', name)
            if m and len(m.group(1)) < 6:
                base_id = 11000 + (year - 2025) * 600 + month * 50
                keep = int(m.group(1)) in range(base_id - 100, base_id + 100)
            else:
                # invoice-number based name (7002xxxxxx): month unknown, keep as a candidate
                keep = True
        elif "uber" in name:
            m = re.search(r'ubereats_(\d+)_', name)
            if m:
                base_id = 11000 + (year - 2025) * 600 + month * 50
                keep = int(m.group(1)) in range(base_id - 200, base_id + 100)

        if keep:
            result.append(f)

    # The same attachment is sometimes downloaded twice under different email numbers
    # (wolt_11870_X.pdf / wolt_11884_X.pdf). Keep one copy, preferring the one with a known date.
    deduped, by_identity = [], {}
    for f in result:
        base = os.path.basename(f)
        m = re.match(r'^(wolt|foodora|ubereats)_\d+_(.+)$', base, re.IGNORECASE)
        if not m or m.group(2).lower() == "email_body.pdf":
            deduped.append(f)
            continue
        identity = (m.group(1).lower(), m.group(2).lower())
        if identity not in by_identity:
            by_identity[identity] = len(deduped)
            deduped.append(f)
        elif base in received_index and os.path.basename(deduped[by_identity[identity]]) not in received_index:
            deduped[by_identity[identity]] = f
    # Official statements first, so equal amounts match the statement rather than a weekly summary
    deduped.sort(key=lambda f: 0 if "_statement" in os.path.basename(f).lower() else 1)
    return deduped

def _handwritten_file(year: int, month: int) -> str:
    return os.path.join(HANDWRITTEN_DIR, f"{year}-{month:02d}.json")


def save_handwritten_data():
    """Save the handwritten amounts of the current month (one file per month, nothing is overwritten)."""
    import json
    try:
        os.makedirs(HANDWRITTEN_DIR, exist_ok=True)
        if handwritten_records:  # never overwrite a month with an empty dict
            with open(_handwritten_file(current_period["year"], current_period["month"]), 'w') as f:
                json.dump(handwritten_records, f, indent=2)
            print(f"[PERSIST] Saved handwritten data for {current_period}: {len(handwritten_records)} partners")
        with open(PERIOD_STATE_FILE, 'w') as f:
            json.dump(current_period, f)
    except Exception as e:
        print(f"[PERSIST] Error saving handwritten data: {e}")


def load_handwritten_data(year: int, month: int) -> dict:
    """Load the handwritten amounts stored for a month ({} if none)."""
    import json
    try:
        path = _handwritten_file(year, month)
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"[PERSIST] Error loading handwritten data: {e}")
    return {}


def set_period(year: int, month: int):
    """Switch the dashboard to another payment month and load that month's handwritten amounts."""
    global handwritten_records
    if current_period["year"] == year and current_period["month"] == month:
        return
    current_period["year"], current_period["month"] = year, month
    handwritten_records = load_handwritten_data(year, month)
    save_handwritten_data()
    print(f"[PERIOD] Now working on {year}-{month:02d} ({len(handwritten_records)} handwritten partners)")


def _invoice_dir() -> str:
    path = os.path.abspath(os.path.join(BASE_DIR, settings.INVOICE_STORAGE_PATH))
    os.makedirs(path, exist_ok=True)
    return path


def _manual_dir() -> str:
    path = os.path.join(os.path.dirname(_invoice_dir()), "manual_invoices")
    os.makedirs(path, exist_ok=True)
    return path


def _period_files_on_disk(year: int, month: int) -> list:
    """Every PDF already on the server that belongs to this payment month."""
    import glob
    files = glob.glob(os.path.join(_invoice_dir(), "*.pdf"))
    seen = {os.path.basename(f) for f in files}
    for mf in glob.glob(os.path.join(_manual_dir(), "*.pdf")):
        if os.path.basename(mf) not in seen:
            files.append(mf)
    return _filter_month_files(files, year, month)


def reconcile_from_disk() -> int:
    """Match the handwritten amounts of the current month against the PDFs already downloaded.
    Blocking (Stripe API + PDF parsing) - call it through asyncio.to_thread from endpoints."""
    global reconciliation_results
    year, month = current_period["year"], current_period["month"]
    files = _period_files_on_disk(year, month)
    try:
        st_payouts = download_stripe_payouts(year, month)
    except Exception as e:
        print(f"[RECONCILE] Stripe payouts unavailable: {e}")
        st_payouts = []
    reconciliation_results = reconcile_invoices(handwritten_records, st_payouts, files)
    print(f"[RECONCILE] {year}-{month:02d}: {len(files)} PDFs, {len(handwritten_records)} handwritten partners")
    return len(files)


@app.on_event("startup")
async def startup_auto_reconcile():
    """On startup, restore the month we were working on and re-match from the PDFs on disk."""
    global handwritten_records
    import json

    year, month = default_period()
    first_run = not os.path.exists(PERIOD_STATE_FILE)
    try:
        if not first_run:
            with open(PERIOD_STATE_FILE) as f:
                saved = json.load(f)
            if _valid_period(saved.get("year"), saved.get("month")):
                year, month = saved["year"], saved["month"]
    except Exception as e:
        print(f"[STARTUP] Could not read saved period: {e}")

    current_period["year"], current_period["month"] = year, month
    handwritten_records = load_handwritten_data(year, month)

    # One-time migration from the old single-file storage
    if first_run and not handwritten_records and os.path.exists(HANDWRITTEN_DATA_FILE):
        try:
            with open(HANDWRITTEN_DATA_FILE) as f:
                handwritten_records = normalise_handwritten(json.load(f))
            print(f"[STARTUP] Migrated legacy handwritten data into {year}-{month:02d}")
        except Exception as e:
            print(f"[STARTUP] Legacy handwritten data unreadable: {e}")
    save_handwritten_data()

    print(f"[STARTUP] Period {year}-{month:02d}, handwritten partners: {len(handwritten_records)}")
    try:
        await asyncio.to_thread(reconcile_from_disk)
    except Exception as e:
        print(f"[STARTUP] Auto-reconcile failed: {e}")

async def daily_auto_sync():
    """
    Keeps the invoices collected without anyone doing anything: every night the server downloads
    the invoices of the month being worked on (the previous calendar month, rolling over by itself
    on the 1st) and re-matches them. The only manual step left is dropping the photo.
    """
    import datetime
    while True:
        now = datetime.datetime.now()
        next_run = now.replace(hour=3, minute=30, second=0, microsecond=0)
        if next_run <= now:
            next_run += datetime.timedelta(days=1)
        await asyncio.sleep((next_run - now).total_seconds())
        try:
            year, month = default_period()
            if not sync_state["running"]:
                print(f"[AUTO-SYNC] Nightly sync for {year}-{month:02d}")
                set_period(year, month)
                sync_state["running"] = True
                sync_state["message"] = "Nightly sync..."
                await run_unified_workflow(year, month)
        except Exception as e:
            print(f"[AUTO-SYNC] failed: {e}")
            sync_state["running"] = False


@app.on_event("startup")
async def start_daily_auto_sync():
    asyncio.create_task(daily_auto_sync())


# --- Background Workflows ---
async def run_unified_workflow(year: int, month: int):
    """Download everything for a payment month, then match it against the handwritten amounts."""
    global reconciliation_results
    print(f"--- Background Sync for {year}-{month:02d} ---")
    sync_state["running"] = True
    try:
        # 1. Collect (blocking network work runs in threads so the API stays responsive)
        sync_state["message"] = "Fetching Stripe payouts..."
        try:
            st_payouts = await asyncio.to_thread(download_stripe_payouts, year, month)
        except Exception as e:
            print(f"WARNING: Stripe payouts failed: {e}")
            st_payouts = []

        sync_state["message"] = "Fetching Wolt / Foodora / Uber invoices from email..."
        try:
            email_files = await asyncio.to_thread(fetch_email_invoices, year, month)
        except Exception as e:
            print(f"WARNING: Email invoice fetch failed: {e}")
            email_files = []

        sync_state["message"] = f"Generating {len(st_payouts)} Stripe payout reports..."
        stripe_pdfs = []
        try:
            stripe_pdfs = await generate_payout_reports([p['id'] for p in st_payouts])
            print(f"Generated {len(stripe_pdfs)} Stripe PDF reports")
        except Exception as e:
            print(f"WARNING: Stripe PDF generation failed: {e}")

        # 2. Reconcile: freshly downloaded files + everything already on disk for this month
        sync_state["message"] = "Matching invoices against handwritten amounts..."
        all_files = list(email_files) + list(stripe_pdfs)
        seen = {os.path.basename(f) for f in all_files}
        for f in _period_files_on_disk(year, month):
            if os.path.basename(f) not in seen:
                all_files.append(f)
        month_files = _filter_month_files(all_files, year, month)

        if current_period["year"] == year and current_period["month"] == month:
            reconciliation_results = await asyncio.to_thread(
                reconcile_invoices, handwritten_records, st_payouts, month_files
            )
        print(f"--- Sync Completed. {len(month_files)} files for {year}-{month:02d} payment period. ---")
        sync_state["message"] = f"Sync complete: {len(month_files)} invoices for {year}-{month:02d}"
    except Exception as e:
        print(f"--- Sync FAILED: {e} ---")
        sync_state["message"] = f"Sync failed: {e}"
    finally:
        sync_state["running"] = False

# --- Endpoints ---
@app.get("/")
def read_root():
    return {"status": "Invoice Processor API is running"}

from fastapi.responses import RedirectResponse

@app.get("/view-file")
def view_file(path: str):
    """
    Serves invoice files directly - no redirect, so CORS and browser open/print/download all work.
    """
    import mimetypes
    from fastapi.responses import FileResponse
    filename = os.path.basename(path)
    full_path = os.path.join(_invoice_dir(), filename)
    if not os.path.exists(full_path):
        full_path = os.path.join(_manual_dir(), filename)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    mime_type, _ = mimetypes.guess_type(full_path)
    return FileResponse(
        path=full_path,
        media_type=mime_type or "application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Cache-Control": "no-cache",
        }
    )

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

def _status_payload(extra: Optional[dict] = None) -> dict:
    payload = {
        "status": "success",
        "records": reconciliation_results,
        "results": reconciliation_results,
        "period": dict(current_period),
        "syncing": sync_state["running"],
        "sync_message": sync_state["message"],
        "has_handwritten": bool(handwritten_records),
        "config": {
            "Stripe": bool(settings.STRIPE_API_KEY),
            "Foodora": bool(settings.EMAIL_USER),
            "UberEats": bool(settings.EMAIL_USER),
            "Wolt": bool(settings.EMAIL_USER),
            "Ework": bool(os.getenv("EWORK_EMAIL_USER") and os.getenv("EWORK_EMAIL_PASS")),
            "Swish": True
        }
    }
    if extra:
        payload.update(extra)
    return payload


@app.post("/upload-paper")
async def upload_paper(file: UploadFile = File(...), year: Optional[int] = None, month: Optional[int] = None):
    """
    Photo of the handwritten sheet -> AI reads the amounts -> matched against the invoices
    of the given payment month (defaults to the month the dashboard is on).
    """
    global handwritten_records
    if not _valid_period(year, month):
        year, month = current_period["year"], current_period["month"]

    upload_dir = os.path.join(BASE_DIR, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    safe_name = os.path.basename(file.filename or "handwritten.jpg")
    file_path = os.path.join(upload_dir, f"{year}-{month:02d}_{safe_name}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    parsed_data = await asyncio.to_thread(process_handwritten_image, file_path)
    if not parsed_data:
        # Do NOT pretend it worked and do not touch the stored amounts
        return _status_payload({
            "ocr_ok": False,
            "message": "Could not read any amounts from this photo. Try a sharper, well-lit photo of the whole sheet.",
        })

    set_period(year, month)
    handwritten_records = normalise_handwritten(parsed_data)
    save_handwritten_data()
    files_found = await asyncio.to_thread(reconcile_from_disk)

    return _status_payload({
        "ocr_ok": True,
        "message": "OCR Complete. Recognition results loaded.",
        "handwritten": handwritten_records,
        "files_found": files_found,
    })

# Hosts an invoice PDF may be fetched from by link (the Uber Eats Manager statement download)
INVOICE_LINK_HOSTS = {"tbgs-static.uber.com"}


class InvoiceLink(BaseModel):
    url: str


@app.post("/upload-invoice-url")
async def upload_invoice_url(link: InvoiceLink, year: Optional[int] = None, month: Optional[int] = None):
    """Add an invoice by pasting its download link (Uber monthly statement link from Uber Eats Manager)."""
    from urllib.parse import urlparse
    import requests
    parsed = urlparse(link.url.strip())
    if parsed.scheme != "https" or parsed.hostname not in INVOICE_LINK_HOSTS:
        raise HTTPException(status_code=400, detail="Only Uber statement links (https://tbgs-static.uber.com/...) are accepted")

    def _download() -> bytes:
        r = requests.get(link.url.strip(), timeout=60, allow_redirects=False)
        if r.status_code != 200 or not r.content.startswith(b"%PDF"):
            raise ValueError(f"HTTP {r.status_code}")
        return r.content

    try:
        content = await asyncio.to_thread(_download)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not download the statement (the link may have expired): {e}")
    name = os.path.basename(parsed.path) or "uber_statement.pdf"
    return await _store_invoice_pdf(content, name, year, month)


@app.post("/upload-invoice")
async def upload_invoice(file: UploadFile = File(...), year: Optional[int] = None, month: Optional[int] = None):
    """
    Add an invoice PDF by hand (e.g. the Uber monthly statement downloaded from the Uber portal,
    which never arrives by email). It is stored for the payment month and matched immediately.
    """
    return await _store_invoice_pdf(await file.read(), file.filename or "invoice.pdf", year, month)


async def _store_invoice_pdf(content: bytes, filename: str, year: Optional[int], month: Optional[int]):
    if not _valid_period(year, month):
        year, month = current_period["year"], current_period["month"]
    original = os.path.basename(filename)
    if not original.lower().endswith(".pdf") or not content.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="Only PDF invoices can be added here")

    tmp_path = os.path.join(_invoice_dir(), f".incoming_{original}")
    with open(tmp_path, "wb") as buffer:
        buffer.write(content)
    text = (await asyncio.to_thread(extract_text_from_pdf, tmp_path)).lower()
    lowered = original.lower()
    if "ework group" in text or lowered.startswith("sbi"):
        tag = "ework"
    elif "uber" in text or "uber" in lowered:
        tag = "ubereats"
    elif "wolt" in text or "wolt" in lowered:
        tag = "wolt"
    elif "foodora" in text or "delivery hero" in text or "foodora" in lowered:
        tag = "foodora"
    else:
        os.remove(tmp_path)
        raise HTTPException(status_code=400, detail="Could not tell which partner this invoice is from (Uber, Wolt, Foodora or Ework)")

    import re
    safe = re.sub(r'[^A-Za-z0-9._ -]', '_', original)
    final_name = f"{tag}_{MONTH_NAMES[month - 1]}{year}_uploaded_{safe}"
    final_path = os.path.join(_invoice_dir(), final_name)
    os.replace(tmp_path, final_path)
    print(f"[UPLOAD-INVOICE] Stored {final_name}")

    set_period(year, month)
    files_found = await asyncio.to_thread(reconcile_from_disk)
    return _status_payload({
        "ocr_ok": True,
        "message": f"Added {tag} invoice for {year}-{month:02d}",
        "stored_as": final_name,
        "files_found": files_found,
    })

class ManualHandwrittenInput(BaseModel):
    """Manual input of handwritten amounts when OCR is not available."""
    records: Dict[str, List[float]]

@app.post("/upload-handwritten-manual")
async def upload_handwritten_manual(data: ManualHandwrittenInput, year: Optional[int] = None, month: Optional[int] = None):
    """
    Manually enter/correct handwritten amounts.
    Example body: {"records": {"Wolt": [3234.64, 1668.34], "Uber": [1017.25]}}
    """
    global handwritten_records
    if not _valid_period(year, month):
        year, month = current_period["year"], current_period["month"]

    set_period(year, month)
    handwritten_records = normalise_handwritten(data.records)
    save_handwritten_data()
    files_found = await asyncio.to_thread(reconcile_from_disk)

    return _status_payload({
        "message": f"Manual records loaded: {len(handwritten_records)} partners, found {files_found} PDFs",
        "handwritten": handwritten_records,
        "files_found": files_found,
    })

@app.get("/reconciliation-status")
async def get_reconciliation_status(year: Optional[int] = None, month: Optional[int] = None):
    """Current matching result. Passing another year/month switches the dashboard to that month."""
    if _valid_period(year, month) and (year, month) != (current_period["year"], current_period["month"]) \
            and not sync_state["running"]:
        set_period(year, month)
        await asyncio.to_thread(reconcile_from_disk)
    return _status_payload()

class MergeRequest(BaseModel):
    file_paths: List[str]


def _build_merged_pdf(file_paths: List[str]):
    """Merge invoices into one PDF and return it as an inline browser response.
    Wolt/Foodora/Uber invoices contribute their first page only (same rule as server printing)."""
    import tempfile
    from pypdf import PdfReader, PdfWriter
    from fastapi.responses import FileResponse

    writer = PdfWriter()
    added, seen = 0, set()
    for raw in file_paths:
        name = os.path.basename(raw or "")
        if name in seen:
            continue
        seen.add(name)
        path = os.path.join(_invoice_dir(), name)
        if not os.path.exists(path):
            path = os.path.join(_manual_dir(), name)
        if not name.lower().endswith(".pdf") or not os.path.exists(path):
            continue
        try:
            reader = PdfReader(path)
            first_page_only = any(p in name.lower() for p in ["wolt", "foodora", "uber", "eats"])
            if "uber" in name.lower() and is_uber_statement(path):
                # Uber monthly statement: overview + one page per payout, without the glossary appendix
                pages = [pg for pg in reader.pages if "Bilaga" not in (pg.extract_text() or "")[:200]]
            elif first_page_only:
                pages = reader.pages[:1]
            else:
                pages = reader.pages
            for page in pages:
                writer.add_page(page)
            added += 1
        except Exception as e:
            print(f"[MERGE] Skipping {name}: {e}")
    if added == 0:
        raise HTTPException(status_code=404, detail="No invoices to print yet for this month")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", prefix="invoices_merged_")
    with open(tmp.name, "wb") as f:
        writer.write(f)
    out_name = f"invoices_{current_period['year']}-{current_period['month']:02d}.pdf"
    return FileResponse(tmp.name, media_type="application/pdf",
                        headers={"Content-Disposition": f'inline; filename="{out_name}"',
                                 "Cache-Control": "no-store"})


@app.post("/merged-pdf")
def merged_pdf(req: MergeRequest):
    """One PDF containing the given invoices (used for a hand-picked selection)."""
    return _build_merged_pdf(req.file_paths)


@app.get("/print-pdf")
async def print_pdf_link(year: Optional[int] = None, month: Optional[int] = None,
                         partner: Optional[str] = None, all: bool = False):
    """
    A plain link that opens ONE PDF ready to print - works in any browser, on any device,
    without popups: the invoices matched to the handwritten amounts of a month
    (optionally one partner; all=true includes that partner's unmatched invoices too).
    """
    if _valid_period(year, month) and (year, month) != (current_period["year"], current_period["month"]) \
            and not sync_state["running"]:
        set_period(year, month)
        await asyncio.to_thread(reconcile_from_disk)

    files = []
    for r in reconciliation_results:
        if partner and r.get("partner", "").lower() != partner.lower():
            continue
        files += [m.get("file") for m in r.get("matches", []) if m.get("file")]
        files += r.get("files", [])
        if all:
            files += r.get("other_files", [])
    return await asyncio.to_thread(_build_merged_pdf, files)

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
async def trigger_download(background_tasks: BackgroundTasks, year: Optional[int] = None, month: Optional[int] = None):
    if not _valid_period(year, month):
        year, month = default_period()
    if sync_state["running"]:
        return {"message": "Sync already running", "period": dict(current_period)}
    set_period(year, month)
    sync_state["running"] = True
    sync_state["message"] = "Starting sync..."
    background_tasks.add_task(run_unified_workflow, year, month)
    return {"message": "Sync started", "period": dict(current_period)}

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
