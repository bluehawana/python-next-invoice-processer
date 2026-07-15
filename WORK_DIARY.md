# Work Diary — Invoice Processing System

## 2026-07-15 — Major Reconciliation Overhaul

### What was broken
- **OCR was fake**: `ocr_module.py` returned hardcoded April 2026 dummy data regardless of what image was uploaded.
- **Reconciliation was fake**: Only matched by filename keyword (wolt/uber/foodora), never compared actual amounts.
- **Stripe PDFs failed**: Playwright browser not installed, so all 18 Stripe payouts had no PDFs.
- **Email date range too narrow**: Only searched from the 1st of the target month, missing invoices for work done in the previous month but paid later (e.g. Foodora Apr 23–30 invoice arriving May 1).
- **Wolt month filter too strict**: Used only the start date of the payout period filename — rejected `2026-04-16__2026-05-01.pdf` for May even though it ends in May.
- **Uber week filter wrong**: Only kept emails where period END month = target month, dropping weeks that span month boundaries (e.g. 4/27–5/10).
- **Stripe sort order wrong**: Payouts returned newest-first from API, printed in wrong order vs handwritten notes.
- **Frontend hardcoded port 8000**: Local dev was hitting another server (oMLX AI server) on 8000.

### What was fixed

#### `backend/ocr_module.py` — Complete rewrite
- **Real PDF amount extraction**: Regex patterns for each partner's PDF format:
  - Foodora: `Vi betalar ut till er (1) + (2) 17,501.19 SEK`
  - Uber: `Total Betalning 1.363.30 kr` (dot-as-thousands format)
  - Wolt: `Belopp utbetalning  2 046,41` (Swedish space+comma format)
  - Stripe: `1,234.56kr SEK` (dot-decimal format)
- **Real reconciliation**: Each handwritten amount is matched to the closest PDF amount within tolerance (50 SEK). Shows exact diff per match.
- **Vision API ready**: Supports OpenAI GPT-4o (`OPENAI_API_KEY`) and Z.AI GLM-4V (`ZAI_API_KEY`) for real handwriting recognition when key is available.

#### `backend/email_module.py`
- **Wider search window**: Now searches from 2 weeks BEFORE target month start, catching delayed invoices.
- **Wolt**: Accept payout reports where EITHER start OR end date is in target month.
- **Uber**: Keep emails where EITHER start OR end month matches target (catches cross-month weeks like 4/27–5/10 for May).

#### `backend/stripe_module.py`
- **Sort payouts by arrival date ascending** (earliest first = matches handwritten note order, starting with 630.90 on Jun 1).
- Added `arrival_ts` field for reliable sorting.

#### `backend/main.py`
- Added `/upload-handwritten-manual` endpoint: POST JSON with partner amounts when OCR isn't available.
  ```json
  {"records": {"Foodora": [17501.19], "Uber": [1363.3], "Wolt": [883.76], "Stripe": [767.81]}}
  ```

#### `frontend/app/page.tsx`
- Fixed local API URL from hardcoded `localhost:8000` → `localhost:8003` (8000 was taken by another service).
- Reconciliation table now shows **actual matched amounts** with diffs:
  - `1363.30 kr → 1363.30 kr (Δ0.00)` ✅
  - `883.76 kr → no invoice found` ❌
- Status badge changed from "Reconciled/Linked" to "Matched/No Match".

#### `backend/monthly_sync.py` — New file
- Script to run on the 10th of each month.
- Calls the API to fetch previous month's invoices, waits for sync, prints summary.
- Saves results to `logs/sync_YYYY-MM.json`.

#### Cron job (macOS)
```
0 8 10 * * cd /backend && python monthly_sync.py >> logs/cron.log 2>&1
```
Auto-runs on 10th of each month at 08:00.

#### `backend/com.bluehawana.invoice-backend.plist` — New file
macOS LaunchAgent service — keeps backend running permanently, auto-restarts on crash, starts on login.
```bash
cp com.bluehawana.invoice-backend.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.bluehawana.invoice-backend.plist
```

### May 2026 Results
| Partner | Matched | Total |
|---------|---------|-------|
| ✅ Stripe | 18/18 | 25,072.92 kr |
| ✅ Foodora | 4/4 | 76,385.57 kr |
| ✅ Wolt | 1/2 | 883.76 kr matched (1451.08 missing — not in email) |
| ⚠️ Uber | 2/4 | 1363.30 + 1121.90 matched (1718.6 + 1099.8 not in Gmail) |

Missing Uber weeks (5/4–5/10 and 5/11–5/17) were never sent by Uber to Gmail.
Manually created PDFs from Uber Merchant portal data.

### June 2026 — In Progress
- Stripe: 17 payouts found, 630.90 confirmed as Jun 1 first payout ✅
- Foodora: 3 invoices in email (22686.20, 16250.99, 8825.21)
- Uber: 3 emails found (1256.45, 951.20, 1289.60)
- Missing: 9667.82 Foodora, 228.8 and 667.55 Uber — not matching any email amounts

### VPS Deployment Notes
- VPS runs backend on port 8000 via systemd `invoice-backend.service`
- After push: `ssh racknerd` then `cd /home/harvad/invoice-processor && bash deployment/deploy_backend.sh`
- Or manually: `sudo systemctl restart invoice-backend`
