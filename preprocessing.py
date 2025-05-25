import cv2
from pdf2image import convert_from_path
from PIL import Image
import os


def preprocess_pdf(input_pdf, output_pdf, dpi=300):
    pages = convert_from_path(input_pdf, dpi=dpi)
    processed_images = []

    for i, page in enumerate(pages):
        img_path = f'page_{i}.png'
        page.save(img_path, 'PNG')

        image = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

        blurred = cv2.GaussianBlur(image, (5, 5), 0)

        adaptive_threshold = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )

        processed_image = Image.fromarray(adaptive_threshold)
        processed_images.append(processed_image)

        os.remove(img_path)

    processed_images[0].save(
        output_pdf,
        save_all=True,
        append_images=processed_images[1:],
        resolution=100.0,
        quality=95
    )
    print(f"Saved preprocessed PDF as {output_pdf}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) not in [3, 4]:
        print("Usage: python preprocessing.py input.pdf output.pdf [dpi]")
    else:
        dpi = int(sys.argv[3]) if len(sys.argv) == 4 else 300
        preprocess_pdf(sys.argv[1], sys.argv[2], dpi=dpi)
