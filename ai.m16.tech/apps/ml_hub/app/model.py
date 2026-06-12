from dataclasses import dataclass

from ultralytics import YOLO

from ml_hub.app.ml_pipe import Node, NodeValue, VALUE_TYPE_INT, VALUE_TYPE_OBJECT_DETECT, VALUE_TYPE_STOP


@dataclass
class Point:
    """
    Координаты точки изображения
    """
    x: int
    y: int


@dataclass
class ObjectDetectData:
    track_id: id
    name: str
    score: float
    point_1: Point
    point_2: Point
    center: Point


class ModelClassification(Node):
    last_class = -1

    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = YOLO(model_path)

    def call(self, value: NodeValue):
        results = self.model(value.data, verbose=False)

        value_class = results[0].probs.top1
        if value_class != self.last_class:
            self.last_class = value_class
            print('class', value_class)

        return NodeValue(type=VALUE_TYPE_INT, data=value_class)

    def string(self):
        return 'ModelClassification(' + self.model_path + ')'


class ModelDetect(Node):
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = YOLO(model_path)

    def call(self, value: NodeValue) -> NodeValue:
        results = self.model(value.data, verbose=False)

        detect_data_items = []
        for (index, boxe) in enumerate(results[0].boxes.xyxy.cpu().numpy()):
            name_index = results[0].boxes.cls[index]
            name = results[0].names[int(name_index)]
            conf = results[0].boxes.conf[index].item()
            x = boxe[2] - boxe[0] / 2
            y = boxe[3] - boxe[1] / 2

            point_1 = Point(x=int(boxe[0]), y=int(boxe[1]))
            point_2 = Point(x=int(boxe[2]), y=int(boxe[3]))

            detect_data = ObjectDetectData(
                track_id=0,
                name=name,
                score=conf,
                point_1=point_1,
                point_2=point_2,
                center=Point(x=int(x), y=int(y))
            )

            detect_data_items.append(detect_data)

        if len(detect_data_items) == 0:
            return NodeValue(type=VALUE_TYPE_STOP)

        return NodeValue(type=VALUE_TYPE_OBJECT_DETECT, data=detect_data_items)

    def string(self):
        return 'ModelDetect(' + self.model_path + ')'

#
# dfg = Image.open('data/2-crop-2/out1.png')
# dfg = asarray(dfg)
#
# image = 'data/ds-2/val/red/out58.png'
#
# path = 'data/model/model-tl.pt'
# m = ModelTrafficLight(path)
# m.detect(image)
