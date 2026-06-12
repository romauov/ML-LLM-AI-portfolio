import cv2

from ml_hub.app.ml_pipe import Node, VALUE_TYPE_IMAGE
from ml_hub.app.ml_pipe import NodeValue

cv2.namedWindow('demo', cv2.WINDOW_NORMAL)
cv2.resizeWindow('demo', 640, 480)


class Camera(Node):

    def __init__(self, video_path: str):
        self.video_path = video_path

    def call(self, value: NodeValue):
        video = cv2.VideoCapture(self.video_path)

        index = 0
        while video.isOpened():
            index += 1
            ret, frame = video.read()
            if ret:
                cv2.imshow('demo', frame)
                if cv2.waitKey(1) == 27:
                    break
                message = NodeValue(type=VALUE_TYPE_IMAGE, data=frame)
                yield message
            else:
                break

    def string(self):
        return 'Camera'
