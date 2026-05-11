import subprocess
import os
import tempfile

def print_pdf(file_path: str):
    """
    Prints a PDF file using the macOS 'lp' command.
    """
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False

    try:
        # 'lp' is the standard printing command on macOS/Unix
        print(f"Sending {file_path} to printer...")
        
        cmd = ["lp"]
        
        # Check if we should only print the first page
        filename = os.path.basename(file_path).lower()
        if any(partner in filename for partner in ["wolt", "foodora", "uber", "eats"]):
            print("limiting to first page...")
            cmd.extend(["-o", "page-ranges=1"])
            
        cmd.append(file_path)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("Print job submitted successfully.")
            return True
        else:
            print(f"Error submitting print job: {result.stderr}")
            return False
    except Exception as e:
        print(f"Failed to print {file_path}: {e}")
        return False

def merge_pdfs(file_paths: list, output_path: str) -> bool:
    """
    Merges multiple PDF files into a single PDF using pypdf.
    Returns True on success, False on failure.
    """
    try:
        from pypdf import PdfWriter
        writer = PdfWriter()
        for path in file_paths:
            if os.path.exists(path):
                writer.append(path)
            else:
                print(f"Skipping missing file: {path}")
        with open(output_path, "wb") as f:
            writer.write(f)
        print(f"Merged {len(file_paths)} PDFs into {output_path}")
        return True
    except ImportError:
        print("pypdf not installed. Run: pip install pypdf")
        return False
    except Exception as e:
        print(f"Failed to merge PDFs: {e}")
        return False

def batch_print_invoices(file_paths: list):
    """
    Prints a list of PDF files.
    - Stripe payout PDFs are merged into a single print job.
    - Wolt/Foodora/Uber PDFs are printed individually (first page only).
    - Other PDFs are printed individually.
    """
    if not file_paths:
        return []

    stripe_files = [f for f in file_paths if "stripe_payout" in os.path.basename(f).lower()]
    other_files  = [f for f in file_paths if "stripe_payout" not in os.path.basename(f).lower()]

    results = []

    # Merge all Stripe PDFs into one job
    if stripe_files:
        if len(stripe_files) == 1:
            results.append(print_pdf(stripe_files[0]))
        else:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", prefix="stripe_merged_")
            tmp.close()
            merged = merge_pdfs(stripe_files, tmp.name)
            if merged:
                print(f"Printing {len(stripe_files)} Stripe payouts as a single job...")
                results.append(print_pdf(tmp.name))
            else:
                # Fallback: print individually
                print("Merge failed, printing Stripe PDFs individually...")
                for path in stripe_files:
                    results.append(print_pdf(path))
            try:
                os.unlink(tmp.name)
            except Exception:
                pass

    # Print non-Stripe files individually (with page-range logic intact)
    for path in other_files:
        results.append(print_pdf(path))

    return results
