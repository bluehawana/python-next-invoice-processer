import subprocess
import os

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

def batch_print_invoices(file_paths: list):
    """
    Prints a list of PDF files.
    """
    results = []
    for path in file_paths:
        results.append(print_pdf(path))
    return results
