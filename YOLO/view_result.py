import cv2
import os

# 🔧 Set these to your file paths
image_path = "image3.jpg"
label_path = "runs/detect/predict12/labels/image3.txt"
output_path = "page003_annotated.jpg"

# 🎨 Define a unique color per class (BGR format)
class_colors = {
    0: (0, 255, 0),      # Green for class 0
    1: (255, 0, 0),      # Blue for class 1
    2: (0, 0, 255)       # Red for class 2
}

# 🔁 Load image
image = cv2.imread(image_path)
h, w, _ = image.shape

# 🧾 Load and draw labels
with open(label_path, "r") as f:
    for line in f:
        parts = line.strip().split()
        cls_id = int(parts[0])
        x_center, y_center, box_w, box_h, conf = map(float, parts[1:])

        # 📐 Convert to absolute pixel values
        x1 = int((x_center - box_w / 2) * w)
        y1 = int((y_center - box_h / 2) * h)
        x2 = int((x_center + box_w / 2) * w)
        y2 = int((y_center + box_h / 2) * h)

        color = class_colors.get(cls_id, (255, 255, 255))  # fallback: white
        label = f"{conf:.2f}"

        # 🟩 Draw box and label
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
        cv2.putText(image, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

# 💾 Save result
cv2.imwrite(output_path, image)
print(f"Saved annotated image to: {output_path}")