import argparse
import torch
from PIL import Image
from pix2tex.cli import LatexOCR


def main():
    parser = argparse.ArgumentParser(description="Convert an equation image to LaTeX.")
    parser.add_argument("image_path", type=str, help="Path to the equation image")
    parser.add_argument("--checkpoint", type=str, default="C:/Users/HYPERPC/Desktop/Проектики на python/ocr project/training model/LaTeX-OCR/checkpoints/pix2tex/pix2tex_e10_step2511.pth", help="Path to model checkpoint")
    parser.add_argument("--config", type=str, default="C:/Users/HYPERPC/Desktop/Проектики на python/ocr project/training model/LaTeX-OCR/pix2tex/model/settings/config.yaml", help="Path to config file")
    parser.add_argument("--temperature", type=float, default=1e-6, help="Sampling temperature")

    args = parser.parse_args()

    # Load model
    model_args = argparse.Namespace(
        checkpoint=args.checkpoint,
        config=args.config,
        temperature=args.temperature,
    )
    #model = LatexOCR(model_args)
    model = LatexOCR()
    img = Image.open(args.image_path).convert("RGB")
    latex_code = model(img)
    print(latex_code)
    return latex_code


if __name__ == "__main__":
    main()
