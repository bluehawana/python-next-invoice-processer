"""
OCR Module - Real handwriting recognition using OpenAI Vision API
and PDF amount extraction for reconciliation.
"""
from typing import List, Dict, Optional, Tuple
import os
import re
import base64
from PIL import Image
import pillow_heif

pillow_heif.register_heif_opener()


# ─────────────────────────────────────────────────────────────
# 1.  PDF text extraction
# ─────────────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from a PDF file using pypdf."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"[PDF] Could not extract text from {os.path.basename(pdf_path)}: {e}")
        return ""


def extract_payout_amount_from_pdf(pdf_path: str, partner: str) -> Optional[float]:
    """
    Extract the payout/net amount from a partner invoice PDF.
    Returns the amount in SEK, or None if not found.
    """
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return None

    filename = os.path.basename(pdf_path).lower()
    print(f"[PDF] Extracting amount from {filename} ({partner})")

    # ── Wolt payout_report ──────────────────────────────────────────────────
    # "Belopp utbetalning  2 046,41"  (Swedish: space=thousands, comma=decimal)
    if "wolt" in partner.lower():
        for pattern in [
            r'Belopp\s+utbetalning\s+([\d\s]+[.,]\d{2})',
            r'Payout\s+amount\s+([\d\s]+[.,]\d{2})',
            r'Total\s+payout\s+([\d\s]+[.,]\d{2})',
            r'Utbetalning\s+([\d\s]+[.,]\d{2})',
        ]:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                return _parse_swedish_number(m.group(1))

    # ── Foodora / faktureringsdokument ──────────────────────────────────────
    # "Vi betalar ut till er (1) + (2) 17,501.19 SEK"
    if "foodora" in partner.lower():
        for pattern in [
            r'Vi\s+betalar\s+ut\s+till\s+er.*?([\d,]+\.\d{2})\s*SEK',
            r'Summa\s+att\s+betala\s+([\d\s,]+[.,]\d{2})',
            r'Att\s+betala\s+([\d\s,]+[.,]\d{2})',
            r'Totalt\s+([\d\s,]+[.,]\d{2})',
        ]:
            m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if m:
                return _parse_dot_number(m.group(1).replace(' ', ''))

    # ── Uber Eats email_body PDF ─────────────────────────────────────────────
    # Generated PDF has "Total Betalning 1.363.30 kr" (dots as thousand seps)
    if "uber" in partner.lower():
        for pattern in [
            r'Total\s+Betalning\s+([\d.]+,\d{2})\s*kr',   # 1.363,30 kr
            r'Total\s+Betalning\s+([\d.]+)\s*kr',          # 1.363.30 kr (two dots)
            r'Nettoförsäljning\s+([\d.]+)\s*kr',
        ]:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                raw = m.group(1)
                # Handle "1.363.30" (two dots) → remove all but last dot
                parts = raw.split('.')
                if len(parts) > 2:
                    raw = ''.join(parts[:-1]) + '.' + parts[-1]
                elif len(parts) == 2 and len(parts[-1]) == 2:
                    raw = parts[0].replace(',', '') + '.' + parts[1]
                else:
                    raw = raw.replace(',', '.')
                try:
                    return float(raw)
                except Exception:
                    pass

    # ── Stripe payout PDF ────────────────────────────────────────────────────
    if "stripe" in partner.lower():
        for pattern in [
            r'([\d,]+\.\d{2})kr\s+SEK',          # top header amount "1,234.56kr SEK"
            r'Payouts\s+([\d,]+\.\d{2})kr',
        ]:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                return _parse_dot_number(m.group(1))

    # ── Generic fallback: last large number on page ─────────────────────────
    # Find all currency-looking numbers and return the largest
    numbers = re.findall(r'([\d\s]{1,10}[.,]\d{2})\s*(?:kr|SEK)', text, re.IGNORECASE)
    if numbers:
        parsed = [_parse_swedish_number(n) for n in numbers]
        parsed = [x for x in parsed if x and 10 < x < 1_000_000]
        if parsed:
            return max(parsed)

    return None


def _parse_swedish_number(s: str) -> Optional[float]:
    """Parse Swedish number format: '1 234,56' or '1234,56' → 1234.56"""
    try:
        cleaned = s.strip().replace('\xa0', '').replace(' ', '')
        # Swedish: comma = decimal, period = thousand sep
        if ',' in cleaned and '.' in cleaned:
            # e.g. 1.234,56
            cleaned = cleaned.replace('.', '').replace(',', '.')
        elif ',' in cleaned:
            cleaned = cleaned.replace(',', '.')
        return float(cleaned)
    except Exception:
        return None


def _parse_dot_number(s: str) -> Optional[float]:
    """Parse dot-decimal format: '1,234.56' → 1234.56"""
    try:
        return float(s.replace(',', ''))
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────
# 2.  OCR – real handwriting recognition via OpenAI vision
# ─────────────────────────────────────────────────────────────

def _encode_image_base64(image_path: str) -> str:
    """Read image (converting HEIC first) and return base64 string."""
    ext = os.path.splitext(image_path)[1].lower()
    if ext in (".heic", ".heif"):
        print(f"[OCR] Converting HEIC: {image_path}")
        img = Image.open(image_path)
        new_path = image_path.rsplit(".", 1)[0] + ".jpg"
        img.save(new_path, "JPEG")
        image_path = new_path

    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _call_vision_api(image_b64: str) -> str:
    """
    Call Z.AI GLM-4.5V vision (OpenAI-compatible) to extract handwritten amounts.
    Falls back to OpenAI gpt-4o if ZAI_API_KEY is not set.
    """
    try:
        import openai

        # Prefer Z.AI, fall back to OpenAI
        zai_key = os.getenv("ZAI_API_KEY")
        oai_key = os.getenv("OPENAI_API_KEY")

        if zai_key:
            print("[OCR] Using Z.AI GLM-4.5V vision model")
            client = openai.OpenAI(
                api_key=zai_key,
                base_url="https://api.z.ai/api/paas/v4",
            )
            model = "glm-4.5v"
        elif oai_key:
            print("[OCR] Using OpenAI GPT-4o vision model")
            client = openai.OpenAI(api_key=oai_key)
            model = "gpt-4o"
        else:
            raise ValueError("Neither ZAI_API_KEY nor OPENAI_API_KEY is set in .env")

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": (
                                "This is a handwritten income record for a Swedish restaurant (Ichiban Sushi). "
                                "Please extract all the amounts listed for each delivery partner. "
                                "The partners are typically: Wolt, Uber Eats (or Uber), Foodora, Stripe (or Hem/Hemleverans), Swish. "
                                "Return ONLY a JSON object like:\n"
                                '{"Wolt": [3234.64, 1668.34], "Uber": [1017.25, 2540.20], "Foodora": [23032.01], "Stripe": [1389.85], "Swish": [129.0]}\n'
                                "Use the amounts exactly as written (convert Swedish format 1 234,56 → 1234.56). "
                                "Ignore any totals/sums rows. "
                                "If a partner has no amounts, omit it. Return valid JSON only, no markdown."
                            )
                        }
                    ]
                }
            ],
            max_tokens=1000,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[OCR] Vision API error: {e}")
        return ""


def _parse_ocr_response(response_text: str) -> Dict[str, List[float]]:
    """Parse the JSON response from the vision model."""
    import json
    # Strip markdown code fences if present
    text = re.sub(r'```(?:json)?', '', response_text).strip()
    # Find the JSON object
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if not m:
        print(f"[OCR] Could not find JSON in response: {response_text[:200]}")
        return {}
    try:
        data = json.loads(m.group(0))
        result = {}
        for k, v in data.items():
            if isinstance(v, list):
                floats = []
                for x in v:
                    try:
                        floats.append(float(x))
                    except Exception:
                        pass
                if floats:
                    result[k] = floats
        return result
    except json.JSONDecodeError as e:
        print(f"[OCR] JSON parse error: {e}\nText: {text[:300]}")
        return {}


def process_handwritten_image(image_path: str) -> Dict[str, List[float]]:
    """
    Processes the handwritten paper image to extract income records.
    Uses Z.AI GLM-4V (ZAI_API_KEY) or OpenAI GPT-4o (OPENAI_API_KEY).
    """
    zai_key = os.getenv("ZAI_API_KEY")
    oai_key = os.getenv("OPENAI_API_KEY")

    if not zai_key and not oai_key:
        print("[OCR] WARNING: No vision API key set (ZAI_API_KEY or OPENAI_API_KEY).")
        return {}

    print(f"[OCR] Processing image: {image_path}")
    try:
        image_b64 = _encode_image_base64(image_path)
        response_text = _call_vision_api(image_b64)
        print(f"[OCR] Vision response: {response_text[:400]}")
        parsed = _parse_ocr_response(response_text)
        if parsed:
            print(f"[OCR] Extracted: { {k: v for k, v in parsed.items()} }")
        else:
            print("[OCR] No records extracted from image.")
        return parsed
    except Exception as e:
        print(f"[OCR] Error processing image: {e}")
        return {}


# ─────────────────────────────────────────────────────────────
# 3.  Reconciliation – match handwritten amounts against PDFs
# ─────────────────────────────────────────────────────────────

def _amounts_match(handwritten: float, pdf_amount: float, tolerance: float = 5.0) -> bool:
    """
    Returns True if the two amounts are within tolerance SEK of each other.
    5 SEK covers minor rounding differences between weekly summaries.
    """
    return abs(handwritten - pdf_amount) <= tolerance


def reconcile_invoices(
    handwritten_data: Dict[str, List[float]],
    stripe_payouts: List[Dict],
    email_files: List[str] = []
) -> List[Dict]:
    """
    Matches handwritten amounts with invoice PDFs.

    Strategy:
    - For each handwritten amount per partner, find the invoice PDF whose
      extracted amount is closest.  Mark matched when within tolerance.
    - Files that have no handwritten counterpart are listed as "Unmatched".
    """
    results = []

    # ── Build partner → file list ─────────────────────────────────────────
    file_map: Dict[str, List[str]] = {}
    seen_basenames: set = set()

    for path in email_files:
        raw_basename = os.path.basename(path).lower().strip()
        if raw_basename in seen_basenames:
            continue
        seen_basenames.add(raw_basename)

        if "wolt" in raw_basename:
            file_map.setdefault("wolt", []).append(path)
        elif "foodora" in raw_basename:
            file_map.setdefault("foodora", []).append(path)
        elif "uber" in raw_basename:
            file_map.setdefault("uber", []).append(path)
        elif "stripe" in raw_basename:
            file_map.setdefault("stripe", []).append(path)
        else:
            print(f"[RECONCILE] Unknown partner for file: {raw_basename}")

    print(f"[RECONCILE] File map: { {k: len(v) for k, v in file_map.items()} }")

    # ── Extract amounts from PDFs once ───────────────────────────────────
    pdf_amounts: Dict[str, List[Tuple[str, float]]] = {}  # partner → [(path, amount)]
    for partner_key, files in file_map.items():
        pdf_amounts[partner_key] = []
        for fpath in files:
            amt = extract_payout_amount_from_pdf(fpath, partner_key)
            pdf_amounts[partner_key].append((fpath, amt))
            print(f"[RECONCILE] {os.path.basename(fpath)} → extracted amount: {amt}")

    # ── Stripe: match against API payout amounts ─────────────────────────
    stripe_amount_map: Dict[float, Dict] = {p["amount"]: p for p in stripe_payouts}

    # ── Match handwritten data ────────────────────────────────────────────
    matched_pdf_paths: set = set()

    for partner_label, hw_amounts in handwritten_data.items():
        partner_key = _normalise_partner_key(partner_label)
        partner_total = sum(hw_amounts)
        matches: List[Dict] = []
        unmatched_hw: List[float] = []

        if partner_key == "stripe":
            # Match each handwritten amount against Stripe payout amounts
            used_stripe = set()
            for hw_amt in hw_amounts:
                best = None
                best_diff = float("inf")
                for sa, payout in stripe_amount_map.items():
                    if sa in used_stripe:
                        continue
                    diff = abs(hw_amt - sa)
                    if diff < best_diff:
                        best_diff = diff
                        best = (sa, payout)
                if best and best_diff <= 5.0:
                    used_stripe.add(best[0])
                    matches.append({"hw": hw_amt, "pdf": best[0], "diff": best_diff, "file": best[1].get("report_url", "")})
                else:
                    unmatched_hw.append(hw_amt)

            # Attach any Stripe PDFs too
            relevant_files = file_map.get("stripe", [])
            for f in relevant_files:
                matched_pdf_paths.add(f)

        else:
            # Match each handwritten amount against extracted PDF amounts
            avail = list(pdf_amounts.get(partner_key, []))
            used_pdfs: set = set()

            for hw_amt in hw_amounts:
                best_path = None
                best_pdf_amt = None
                best_diff = float("inf")

                for idx, (fpath, pdf_amt) in enumerate(avail):
                    if idx in used_pdfs or pdf_amt is None:
                        continue
                    diff = abs(hw_amt - pdf_amt)
                    if diff < best_diff:
                        best_diff = diff
                        best_path = fpath
                        best_pdf_amt = pdf_amt
                        best_idx = idx

                if best_path and best_diff <= 50.0:  # wider tolerance for Foodora/Wolt weekly
                    used_pdfs.add(best_idx)
                    matched_pdf_paths.add(best_path)
                    matches.append({"hw": hw_amt, "pdf": best_pdf_amt, "diff": best_diff, "file": best_path})
                else:
                    unmatched_hw.append(hw_amt)
                    # Still attach the closest file (so it's visible)
                    if best_path:
                        matched_pdf_paths.add(best_path)

            relevant_files = [m["file"] for m in matches if m.get("file")]
            # Also add ALL files for this partner so user can see them
            for fpath, _ in avail:
                if fpath not in relevant_files:
                    relevant_files.append(fpath)

        fully_reconciled = (len(matches) == len(hw_amounts) and len(hw_amounts) > 0)

        results.append({
            "partner": partner_label,
            "handwritten_total": partner_total,
            "handwritten_count": len(hw_amounts),
            "matched_count": len(matches),
            "reconciled": fully_reconciled,
            "amounts": hw_amounts,
            "matches": matches,
            "unmatched": unmatched_hw,
            "files": relevant_files,
        })

    # ── Add files found in email that had no handwritten entry ────────────
    accounted_keys = {_normalise_partner_key(k) for k in handwritten_data.keys()}
    for partner_key, files in file_map.items():
        if partner_key not in accounted_keys:
            extracted = pdf_amounts.get(partner_key, [])
            results.append({
                "partner": partner_key.capitalize() + " (no handwritten record)",
                "handwritten_total": 0,
                "handwritten_count": 0,
                "matched_count": 0,
                "reconciled": False,
                "amounts": [],
                "matches": [],
                "unmatched": [],
                "files": files,
                "pdf_amounts": [amt for _, amt in extracted if amt],
            })

    return results


def _normalise_partner_key(label: str) -> str:
    """Map display labels to canonical keys."""
    label_lower = label.lower()
    if "wolt" in label_lower:
        return "wolt"
    if "uber" in label_lower:
        return "uber"
    if "foodora" in label_lower:
        return "foodora"
    if "stripe" in label_lower or "hem" in label_lower:
        return "stripe"
    if "swish" in label_lower:
        return "swish"
    return label_lower.split()[0]
