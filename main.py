import os
import sys
import tempfile
import zipfile
import shutil

from preprocessing import preprocess_pdf
from mathpix import mathpix_pdf_to_tex_zip
from preambula_adder import replace_with_custom_preamble
from llm_proofread import main as llm_proofread


def extract_zip(zip_path, extract_dir):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    subfolders = [os.path.join(extract_dir, f) for f in os.listdir(extract_dir)
                  if os.path.isdir(os.path.join(extract_dir, f))]
    if not subfolders:
        raise RuntimeError("No folder found in Mathpix output structure after extraction.")
    return subfolders[0]


def pipeline(input_pdf, app_id, app_key, output_folder="output"):
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"[Step 1] Preprocessing PDF...")
        preproc_pdf = os.path.join(tmpdir, "preprocessed.pdf")
        preprocess_pdf(input_pdf, preproc_pdf)

        print(f"[Step 2] Sending to Mathpix for LaTeX conversion...")
        zip_path = mathpix_pdf_to_tex_zip(preproc_pdf, app_id, app_key, os.path.join(tmpdir, "mathpix.tex.zip"))

        print(f"[Step 3] Extracting Mathpix archive to output folder...")
        if os.path.exists(output_folder):
            shutil.rmtree(output_folder)
        os.makedirs(output_folder, exist_ok=True)
        mathpix_subfolder = extract_zip(zip_path, output_folder)

        orig_tex_files = [f for f in os.listdir(mathpix_subfolder) if f.endswith('.tex')]
        if not orig_tex_files:
            raise RuntimeError("No .tex file found inside the Mathpix output folder.")
        orig_tex_path = os.path.join(mathpix_subfolder, orig_tex_files[0])

        print(f"[Step 4] Adding custom LaTeX preamble...")
        preamble_tex_path = os.path.join(tmpdir, "with_preamble.tex")
        replace_with_custom_preamble(orig_tex_path, preamble_tex_path)

        print(f"[Step 5] Proofreading LaTeX file with LLM...")
        llm_proofread(preamble_tex_path)

        corrected_dir = os.path.dirname(preamble_tex_path)
        candidates = [os.path.join(corrected_dir, f)
                      for f in os.listdir(corrected_dir)
                      if f.startswith("corrected_") and f.endswith(".tex")]
        candidates += [os.path.join(os.getcwd(), f)
                       for f in os.listdir(os.getcwd())
                       if f.startswith("corrected_") and f.endswith(".tex")]

        if not candidates:
            raise RuntimeError("No corrected .tex file produced by LLM step.")
        corrected_tex = candidates[0]

        shutil.copy(corrected_tex, orig_tex_path)
        print(f"All done! Your output is in the folder:\n  {mathpix_subfolder}\nwith corrected .tex and all assets.")

        for f in os.listdir(output_folder):
            path = os.path.join(output_folder, f)
            if f.endswith('.tex') and os.path.isfile(path):
                os.remove(path)
            if f.endswith('.zip') and os.path.isfile(path):
                os.remove(path)

        for c in candidates:
            try:
                os.remove(c)
            except Exception:
                pass


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py input.pdf [output_folder]")
        sys.exit(1)

    app_id = os.getenv("MATHPIX_APP_ID")
    app_key = os.getenv("MATHPIX_APP_KEY")
    output_folder = sys.argv[2] if len(sys.argv) > 2 else "output"
    pipeline(sys.argv[1], app_id, app_key, output_folder)
