#!/usr/bin/env python3
"""
Monthly invoice sync script.
Runs on the 10th of each month to collect invoices from the previous month.
Triggered by cron: 0 8 10 * * (08:00 on the 10th)

Usage: python monthly_sync.py [year] [month]
       python monthly_sync.py          ← auto-detects previous month
"""
import sys
import os
import asyncio
import datetime
import requests
import json

# ── Config ────────────────────────────────────────────────────────────────────
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
API_BASE    = "http://localhost:8003"
LOG_FILE    = os.path.join(SCRIPT_DIR, "logs", "monthly_sync.log")

os.makedirs(os.path.join(SCRIPT_DIR, "logs"), exist_ok=True)

# ── Logging ───────────────────────────────────────────────────────────────────
def log(msg: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    # Determine target month
    if len(sys.argv) >= 3:
        year  = int(sys.argv[1])
        month = int(sys.argv[2])
    else:
        # Default: previous month
        today = datetime.date.today()
        first_of_this = today.replace(day=1)
        last_month    = first_of_this - datetime.timedelta(days=1)
        year  = last_month.year
        month = last_month.month

    month_label = f"{year}-{month:02d}"
    log(f"=== Monthly sync starting for {month_label} ===")

    # 1. Check API is up
    try:
        r = requests.get(f"{API_BASE}/", timeout=10)
        r.raise_for_status()
        log("API is running ✓")
    except Exception as e:
        log(f"ERROR: API not reachable at {API_BASE}: {e}")
        log("Make sure the backend server is running.")
        sys.exit(1)

    # 2. Trigger invoice download + reconciliation
    log(f"Triggering download for {month_label}...")
    try:
        r = requests.post(
            f"{API_BASE}/trigger-download",
            params={"year": year, "month": month},
            timeout=30
        )
        r.raise_for_status()
        log(f"Download triggered: {r.json().get('message')}")
    except Exception as e:
        log(f"ERROR triggering download: {e}")
        sys.exit(1)

    # 3. Wait for sync to complete (poll up to 3 minutes)
    log("Waiting for sync to complete...")
    import time
    last_count = -1
    for i in range(36):  # 36 × 5s = 3 minutes
        time.sleep(5)
        try:
            r = requests.get(f"{API_BASE}/reconciliation-status", timeout=10)
            data = r.json()
            records = data.get("records", [])
            total_files = sum(len(rec.get("files", [])) for rec in records)
            if total_files != last_count:
                log(f"  Progress: {total_files} invoice files found so far...")
                last_count = total_files
        except Exception:
            pass

    # 4. Get final results
    try:
        r = requests.get(f"{API_BASE}/reconciliation-status", timeout=10)
        data = r.json()
        records = data.get("records", [])
    except Exception as e:
        log(f"ERROR getting results: {e}")
        sys.exit(1)

    # 5. Print summary
    log(f"\n{'='*55}")
    log(f"SYNC COMPLETE for {month_label}")
    log(f"{'='*55}")

    all_files = []
    unmatched_partners = []

    for rec in records:
        partner  = rec["partner"]
        matched  = rec["matched_count"]
        total    = rec["handwritten_count"]
        files    = rec.get("files", [])
        status   = "✅" if rec["reconciled"] else ("⚠️ " if matched > 0 else "❌")

        log(f"{status} {partner}: {matched}/{total} matched, {len(files)} invoice(s)")

        for m in rec.get("matches", []):
            log(f"     {m['hw']:.2f} → {m.get('pdf', 'linked')} (Δ{m.get('diff', 0):.2f})")

        for u in rec.get("unmatched", []):
            log(f"     ❓ {u:.2f} kr — no invoice found in email")
            unmatched_partners.append(f"{partner}: {u:.2f} kr")

        all_files.extend(files)

    log(f"\nTotal invoice files: {len(all_files)}")

    if unmatched_partners:
        log(f"\n⚠️  MISSING INVOICES ({len(unmatched_partners)}):")
        for u in unmatched_partners:
            log(f"   - {u}")
        log("   → Check email manually or wait for delayed delivery")
    else:
        log("\n🎉 All handwritten amounts matched to invoices!")

    log(f"{'='*55}\n")

    # 6. Save results to JSON for reference
    result_path = os.path.join(SCRIPT_DIR, "logs", f"sync_{month_label}.json")
    with open(result_path, "w") as f:
        json.dump({"month": month_label, "records": records, "files": all_files}, f, indent=2, default=str)
    log(f"Results saved to {result_path}")


if __name__ == "__main__":
    main()
