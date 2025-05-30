from ultralytics import YOLO
import torch


def main():
    model = YOLO("yolo11l.pt")

    model.train(data="data.yaml", epochs=500, imgsz=1024, device='cuda', batch=32, cache=True)

if __name__ == "__main__":
    main()
