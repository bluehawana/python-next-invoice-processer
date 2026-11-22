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
            r'Nettoutbetalning\s+([\d\s,]+)\s*kr',  # Nettoutbetalning 2 956,85 kr
            r'Total\s+Betalning\s+([\d.]+)\s*kr',          # 1.363.30 kr (two dots)
            r'Nettoförsäljning\s+([\d.]+)\s*kr',
        ]:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                raw = m.group(1)
                # Handle Swedish format: spaces and comma (2 956,85)
                raw = raw.replace(' ', '').replace('\xa0', '')
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


def extract_payout_amounts_from_pdf(pdf_path: str, partner: str) -> List[float]:
    """
    All payout amounts found in an invoice PDF.
    Usually one, but the Uber monthly statement ("Månadsutdrag") lists every weekly
    payout of the month on its own page ("Nettoutbetalning  2 178,80 kr").
    """
    if "uber" in partner.lower():
        text = extract_text_from_pdf(pdf_path)
        payouts = []
        for raw in re.findall(r'Nettoutbetalning\s+([\d\s\xa0]+,\d{2})\s*kr', text):
            amt = _parse_swedish_number(raw)
            if amt is not None:
                payouts.append(amt)
        if len(payouts) > 1:
            print(f"[PDF] {os.path.basename(pdf_path)}: Uber statement with {len(payouts)} payouts {payouts}")
            return payouts
    single = extract_payout_amount_from_pdf(pdf_path, partner)
    return [single] if single is not None else []


def is_uber_statement(pdf_path: str) -> bool:
    """True for the multi-payout Uber monthly statement."""
    try:
        return len(extract_payout_amounts_from_pdf(pdf_path, "uber")) > 1
    except Exception:
        return False


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
    """Normalise any photo (HEIC/PNG/JPG, any size/rotation) to a JPEG and return it base64-encoded."""
    import io
    from PIL import ImageOps
    img = Image.open(image_path)
    img = ImageOps.exif_transpose(img).convert("RGB")
    img.thumbnail((2400, 2400))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=90)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


OCR_PROMPT = (
    "This photo is a handwritten income record for a Swedish restaurant (Ichiban Sushi). "
    "Each row starts with a label followed by a colon and a comma-separated list of amounts in SEK. "
    "A row can wrap onto the following lines: amounts on a line WITHOUT a label belong to the label above. "
    "Use these exact keys for the known partners:\n"
    '- "Foodora"\n'
    '- "Uber" (written as uber / uber eats)\n'
    '- "Wolt"\n'
    '- "Stripe" (written as hemsida / hem / hemleverans / website / stripe - the long list of small amounts)\n'
    '- "Swish"\n'
    "Any other label (for example Ework) keeps the name as written.\n"
    "Read every digit carefully and copy each amount exactly as written, in order, "
    "using a dot as the decimal separator (1 234,56 -> 1234.56). Do not skip, merge or round amounts. "
    "Ignore totals/sums rows and anything crossed out.\n"
    "Return ONLY a JSON object, no markdown, like:\n"
    '{"Foodora": [23032.01], "Uber": [1017.25, 2540.2], "Wolt": [3234.64, 1668.34], "Stripe": [1389.85, 129.0]}'
)


def _vision_providers() -> List[Dict]:
    """Vision models to try, in order. Cloud models first - they read handwriting far better."""
    providers = []
    zai_key = os.getenv("ZAI_API_KEY")
    oai_key = os.getenv("OPENAI_API_KEY")
    if zai_key:
        providers.append({
            "name": "Z.AI glm-4.5v",
            "api_key": zai_key,
            "base_url": "https://api.z.ai/api/paas/v4",
            "model": "glm-4.5v",
            # glm-4.5v "thinks" by default and burns the whole token budget on reasoning,
            # returning an EMPTY answer. Thinking must be off for OCR.
            "extra_body": {"thinking": {"type": "disabled"}},
        })
    if oai_key:
        providers.append({
            "name": "OpenAI gpt-4o",
            "api_key": oai_key,
            "base_url": None,
            "model": "gpt-4o",
            "extra_body": None,
        })
    ollama_host = os.getenv("OLLAMA_HOST")
    if ollama_host:  # only when explicitly configured
        providers.append({
            "name": "Ollama llava:13b",
            "api_key": "ollama",
            "base_url": f"{ollama_host}/v1",
            "model": "llava:13b",
            "extra_body": None,
        })
    return providers


def _call_vision_api(image_b64: str) -> str:
    """
    Ask a vision model to read the handwritten sheet.
    Tries each configured provider until one returns a parseable, non-empty answer.
    """
    import openai

    providers = _vision_providers()
    if not providers:
        print("[OCR] No vision API configured: set ZAI_API_KEY or OPENAI_API_KEY")
        return ""

    for prov in providers:
        try:
            print(f"[OCR] Trying {prov['name']}")
            kwargs = {"api_key": prov["api_key"], "timeout": 90}
            if prov["base_url"]:
                kwargs["base_url"] = prov["base_url"]
            client = openai.OpenAI(**kwargs)
            extra = {"extra_body": prov["extra_body"]} if prov["extra_body"] else {}
            response = client.chat.completions.create(
                model=prov["model"],
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                        {"type": "text", "text": OCR_PROMPT},
                    ],
                }],
                max_tokens=4000,
                temperature=0,
                **extra,
            )
            text = (response.choices[0].message.content or "").strip()
            if text and _parse_ocr_response(text):
                print(f"[OCR] ✓ {prov['name']} answered")
                return text
            print(f"[OCR] {prov['name']} returned nothing usable "
                  f"(finish_reason={response.choices[0].finish_reason}), trying next provider")
        except Exception as e:
            print(f"[OCR] {prov['name']} failed: {e}")
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
    Uses Ollama (local), Z.AI GLM-4V, or OpenAI GPT-4o (in that order).
    """
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

MATCH_TOLERANCE_SEK = 5.0


def _digit_distance(a: str, b: str) -> int:
    """Edit distance between two amount strings (number of digits inserted/removed/changed)."""
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


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
            amts = extract_payout_amounts_from_pdf(fpath, partner_key)
            if not amts:
                pdf_amounts[partner_key].append((fpath, None))
            for amt in amts:  # one entry per payout inside the PDF
                pdf_amounts[partner_key].append((fpath, amt))
            print(f"[RECONCILE] {os.path.basename(fpath)} → extracted amounts: {amts}")

    # ── Stripe: match against API payout amounts ─────────────────────────

    # Build Stripe PDF file map (payout_id -> file_path)
    stripe_pdf_map: Dict[str, str] = {}
    for fpath in file_map.get("stripe", []):
        # Extract payout ID from filename like: stripe_payout_po_1U09ZJGByRYD7y4lXBZdsWTv.pdf
        import re
        match = re.search(r'stripe_payout_(po_\w+)\.pdf', os.path.basename(fpath))
        if match:
            payout_id = match.group(1)
            stripe_pdf_map[payout_id] = fpath

    # ── Match handwritten data ────────────────────────────────────────────
    matched_pdf_paths: set = set()

    for partner_label, hw_amounts in handwritten_data.items():
        partner_key = _normalise_partner_key(partner_label)
        partner_total = sum(hw_amounts)
        matches: List[Dict] = []
        unmatched_hw: List[float] = []
        near_misses: List[Dict] = []   # closest invoice for each unmatched amount (shown, never printed)

        if partner_key == "stripe":
            # Pass 1: each handwritten amount against the real Stripe payouts (closest, within 5 SEK)
            used_stripe: set = set()   # indexes into stripe_payouts
            pending: List[Tuple[int, float]] = []
            slots: List[Optional[Dict]] = [None] * len(hw_amounts)

            def _stripe_match(i, hw_amt, idx, corrected=False):
                payout = stripe_payouts[idx]
                used_stripe.add(idx)
                pdf_path = stripe_pdf_map.get(payout.get("id", ""), payout.get("report_url", ""))
                slots[i] = {"hw": hw_amt, "pdf": payout["amount"], "diff": abs(hw_amt - payout["amount"]),
                            "file": pdf_path, "corrected": corrected}

            for i, hw_amt in enumerate(hw_amounts):
                best_idx, best_diff = None, float("inf")
                for idx, payout in enumerate(stripe_payouts):
                    if idx in used_stripe:
                        continue
                    diff = abs(hw_amt - payout["amount"])
                    # "<=": payouts are sorted by date, so when two payouts have the same amount
                    # the LATER one wins (the earlier one belongs to the previous month's sheet)
                    if diff < best_diff or (diff == best_diff and best_idx is not None):
                        best_idx, best_diff = idx, diff
                if best_idx is not None and best_diff <= 5.0:
                    _stripe_match(i, hw_amt, best_idx)
                else:
                    pending.append((i, hw_amt))

            # Pass 2: a single misread/missing digit (360.72 vs 3610.72, 1193.23 vs 193.23).
            # Only accepted when exactly ONE unused payout is that close, so it cannot guess.
            for i, hw_amt in pending:
                candidates = [idx for idx, payout in enumerate(stripe_payouts)
                              if idx not in used_stripe
                              and _digit_distance(f"{hw_amt:.2f}", f"{payout['amount']:.2f}") <= 1]
                distinct = {stripe_payouts[idx]["amount"] for idx in candidates}
                if len(distinct) == 1:
                    _stripe_match(i, hw_amt, candidates[0], corrected=True)

            for i, hw_amt in enumerate(hw_amounts):
                if slots[i]:
                    matches.append(slots[i])
                else:
                    unmatched_hw.append(hw_amt)

            # Attach any Stripe PDFs too
            # Only the payouts written on the sheet are listed/printed. The API also returns the
            # payouts of the last two weeks of the previous month; those are kept aside.
            relevant_files = []
            for m in matches:
                f = m.get("file")
                if f and os.path.exists(f) and f not in relevant_files:
                    relevant_files.append(f)
            other_files = [f for f in (stripe_pdf_map.get(p.get("id", "")) for p in stripe_payouts)
                           if f and f not in relevant_files]
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

                # Tight tolerance: a "match" must be the same payout, not merely a similar amount.
                # (50 SEK used to hide wrong invoices: 1817.75 was "matched" to 1840.50.)
                if best_path and best_diff <= MATCH_TOLERANCE_SEK:
                    used_pdfs.add(best_idx)
                    matched_pdf_paths.add(best_path)
                    matches.append({"hw": hw_amt, "pdf": best_pdf_amt, "diff": best_diff, "file": best_path})
                else:
                    unmatched_hw.append(hw_amt)
                    if best_path:
                        matched_pdf_paths.add(best_path)
                        near_misses.append({"hw": hw_amt, "pdf": best_pdf_amt, "diff": best_diff, "file": best_path})

            # Only invoices that matched a handwritten amount are listed/printed
            relevant_files = []
            for m in matches:
                if m.get("file") and m["file"] not in relevant_files:
                    relevant_files.append(m["file"])
            other_files = []
            for fpath, _ in avail:
                if fpath not in relevant_files and fpath not in other_files:
                    other_files.append(fpath)

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
            "near_misses": near_misses,
            "files": relevant_files,
            "other_files": other_files,   # collected for the period but not on the sheet
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


def canonical_partner_label(label: str) -> str:
    """Map whatever was written/recognised ("uber eats", "hemsida", ...) to the display label."""
    key = _normalise_partner_key(label)
    return {"wolt": "Wolt", "uber": "Uber", "foodora": "Foodora", "stripe": "Stripe", "swish": "Swish"}.get(
        key, label.strip()
    )


def normalise_handwritten(data: Dict[str, List[float]]) -> Dict[str, List[float]]:
    """Canonicalise partner labels and merge rows that map to the same partner."""
    result: Dict[str, List[float]] = {}
    for label, amounts in data.items():
        result.setdefault(canonical_partner_label(label), []).extend(amounts)
    return result


def _normalise_partner_key(label: str) -> str:
    """Map display labels to canonical keys."""
    label_lower = label.lower().strip()
    if not label_lower:
        return "unknown"
    if "wolt" in label_lower:
        return "wolt"
    if "uber" in label_lower:
        return "uber"
    if "foodora" in label_lower:
        return "foodora"
    if "stripe" in label_lower or "hem" in label_lower or "website" in label_lower or label_lower.startswith("hers"):
        return "stripe"
    if "swish" in label_lower:
        return "swish"
    return label_lower.split()[0]
