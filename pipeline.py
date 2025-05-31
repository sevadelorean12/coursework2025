import os
import cv2
import argparse
import torch
from PIL import Image
import pytesseract
from pix2tex.cli import LatexOCR
import re

IMAGE_PATH = "test yolo/image4.jpg"
YOLO_TXT_PATH = "test yolo/runs/detect/predict13/labels/image4.txt"
MODEL_CHECKPOINT = "C:/Users/HYPERPC/Desktop/Проектики на python/ocr project/training model/LaTeX-OCR/checkpoints/pix2tex/pix2tex_e10_step2511.pth"
CONFIG_PATH = "C:/Users/HYPERPC/Desktop/Проектики на python/ocr project/training model/LaTeX-OCR/pix2tex/model/settings/config.yaml"
OUTPUT_TEX = "output.tex"

custom_preamble = r"""\documentclass[10pt]{article}
\usepackage{ucharclasses}
\usepackage{amsmath, amsfonts, amssymb}
\usepackage[version=4]{mhchem}
\usepackage{stmaryrd}
\usepackage{bbold}
\usepackage{graphicx}
\usepackage[export]{adjustbox}
\usepackage{polyglossia}
\usepackage{fontspec}
\IfFontExistsTF{CMU Serif}
  {\newfontfamily\lgcfont{CMU Serif}}
  {\IfFontExistsTF{DejaVu Sans}
    {\newfontfamily\lgcfont{DejaVu Sans}}
    {\newfontfamily\lgcfont{Georgia}}}
\setDefaultTransitions{\lgcfont}{}
\graphicspath{{./images/}}
"""


def load_yolo(txt_path, W, H):
    dets = []
    with open(txt_path) as f:
        for line in f:
            cls, xc, yc, w, h, conf = map(float, line.split())
            x1 = int((xc - w/2) * W)
            y1 = int((yc - h/2) * H)
            x2 = int((xc + w/2) * W)
            y2 = int((yc + h/2) * H)
            dets.append({
                "class": int(cls),
                "bbox": (x1,y1,x2,y2),
                "xc": xc, "yc": yc
            })
    dets.sort(key=lambda d: (int(d["yc"]*H//50), d["xc"]*W))
    return dets


def balance_braces(latex: str) -> str:
    opens = latex.count('{')
    closes = latex.count('}')
    if opens > closes:
        latex = latex + '}' * (opens - closes)
    elif closes > opens:
        latex = '{' * (closes - opens) + latex
    return latex


def strip_array_env(latex: str) -> str:
    latex = re.sub(r"\\begin\{array\}\{[^\}]*\}", "", latex)
    latex = latex.replace(r"\end{array}", "")
    return latex


def main():
    p = argparse.ArgumentParser(description="Merge YOLO+OCR+Pix2Tex into a .tex")
    p.add_argument("--image",      required=True, help="Full-page image")
    p.add_argument("--yolo",       required=True, help="YOLO txt detections")
    p.add_argument("--checkpoint", required=True, help="Pix2Tex .pth checkpoint")
    p.add_argument("--config",     required=True, help="Pix2Tex config.yaml")
    p.add_argument("--output_dir", required=True, help="Where to write output.tex + images/")
    p.add_argument("--temp",       type=float, default=1e-6, help="Pix2Tex temperature")
    args = p.parse_args()

    img = cv2.imread(args.image)
    H, W = img.shape[:2]

    os.makedirs(args.output_dir, exist_ok=True)
    images_dir = os.path.join(args.output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    dets = load_yolo(args.yolo, W, H)

    model_args = argparse.Namespace(
        checkpoint=args.checkpoint,
        config=args.config,
        temperature=args.temp,
    )
    #pix2tex = LatexOCR(model_args)
    pix2tex = LatexOCR()
    lines = []
    img_cnt = 0
    for det in dets:
        x1,y1,x2,y2 = det["bbox"]
        crop = img[y1:y2, x1:x2]
        pil = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))

        if det["class"] == 0:  # equation
            raw = pix2tex(pil).strip()
            latex = balance_braces(strip_array_env(raw))
            lines.append(fr"\\{balance_braces(latex)}\\")
        elif det["class"] == 1:  # text
            txt = pytesseract.image_to_string(pil, lang="rus+eng", config="--psm 6").strip()
            lines.append(txt)
        else:  # image
            img_cnt += 1
            fn = f"img_{img_cnt:03d}.png"
            pil.save(os.path.join(images_dir, fn))
            lines.append(f"\\begin{{figure}}[h]\n\\centering\n"
                         f"\\includegraphics[width=0.8\\linewidth]{{images/{fn}}}\n"
                         f"\\end{{figure}}")

    tex_path = os.path.join(args.output_dir, "output.tex")
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(custom_preamble + '\n')
        f.write(r"\setdefaultlanguage{russian}" + "\n")
        f.write(r"\setotherlanguages{english}" + "\n")
        f.write("\\begin{document}\n\n")
        for l in lines:
            f.write(l + "\n\n")
        f.write("\\end{document}\n")

    print(f"Wrote to: {tex_path}")

if __name__=="__main__":
    main()
