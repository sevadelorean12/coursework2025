from ultralytics import YOLO
import torch


def main():
    model = YOLO("yolo11l.pt")

    # Load a model
    model = YOLO("runs/detect/train4/weights/last.pt")  # load a partially trained model

    # Resume training
    results = model.train(epochs=300, resume=True)

if __name__ == "__main__":
    main()
