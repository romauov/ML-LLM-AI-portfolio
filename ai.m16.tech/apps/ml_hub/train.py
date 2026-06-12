from ultralytics import YOLO


def train_traffic_light():
    model = YOLO('yolov8n-cls.pt')
    model.train(
        data="./data/ds-2",
        epochs=50,
        batch=10,
    )
