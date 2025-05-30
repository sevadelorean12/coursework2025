from ultralytics import YOLO

model = YOLO('runs/detect/train4/weights/last.pt')

results = model.predict("image3.jpg", save=True, conf=0.4, save_txt=True, save_conf=True)
