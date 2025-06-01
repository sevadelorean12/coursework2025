import os
import time
import logging
import re
from openai import OpenAI

MODEL = "gpt-4o"
RETRY_LIMIT = 3
RATE_LIMIT_SECONDS = 1.5

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("latex_proofread.log"),
        logging.StreamHandler()
    ]
)


def get_response(fragment, client, model=MODEL, max_tokens=2048):
    prompt = (
        "Fix only grammatical errors in the following LaTeX fragment. "
        "Do not rephrase or change content. Preserve all LaTeX formatting. "
        "Return only the corrected LaTeX text:\n" + fragment
    )

    system_prompt = (
        "You are a LaTeX proofreader. Your task is to review LaTeX content containing possible "
        "grammatical or spelling mistakes in the natural language text portions only. "
        "If you find grammatical or spelling errors in the text portions, correct them. "
        "Use context to correct grammatical or spelling mistakes. "
        "Do not modify any LaTeX commands, environments, math expressions, labels, citations, or formatting. "
        "Output only the corrected LaTeX code without any commentary or explanation. "
        r"Never add \end{document} to the output, even if it seems missing. Do not delete existing \end{document}."
        "Do not add any markdown code fences like ```latex or ``` around the output. "
        "Never replace Latin letters inside math expressions with Cyrillic letters."
    )

    for attempt in range(RETRY_LIMIT):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.warning(f"API error on attempt {attempt + 1}: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff
    logging.error("Max retries reached for a fragment.")
    return fragment


def split_latex_fragments(text):
    fragments = re.split(r"(\n\s*\n)", text)
    out = []
    buf = ""
    for frag in fragments:
        buf += frag
        if frag.strip() == "":
            if buf.strip():
                out.append(buf)
                buf = ""
    if buf.strip():
        out.append(buf)
    return [x for x in out if x.strip()]


def main(input_path):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logging.error("OPENAI_API_KEY not set in environment.")
        return
    client = OpenAI(api_key=api_key)

    base_name = os.path.basename(input_path)
    output_path = f"corrected_{base_name}"

    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    logging.info("Splitting LaTeX document into fragments...")
    fragments = split_latex_fragments(content)
    logging.info(f"Total fragments: {len(fragments)}")

    corrected_fragments = []
    for i, frag in enumerate(fragments):
        frag = frag.strip("\n")
        if not frag:
            continue
        logging.info(f"Correcting fragment {i+1}/{len(fragments)}...")
        corrected = get_response(frag, client)
        if corrected == frag:
            logging.warning(f"No change or API error for fragment {i+1}")
        if len(corrected.split()) < 0.7 * len(frag.split()):
            logging.error(f"Fragment {i+1} may be truncated. Input length: {len(frag)}, Output length: {len(corrected)}")
        corrected_fragments.append(corrected)
        time.sleep(RATE_LIMIT_SECONDS)

    corrected_content = "\n\n".join(corrected_fragments)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(corrected_content)
    logging.info(f"Corrected file saved as {output_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Grammatical correction for LaTeX via OpenAI API.")
    parser.add_argument("input_file", help="Path to the LaTeX .tex file")
    args = parser.parse_args()
    main(args.input_file)
