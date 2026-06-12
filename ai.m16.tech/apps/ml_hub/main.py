from app.action import ActionSendMessage
from app.camera import Camera
from app.filter import ObjectClassFilter, ObjectPositionFilter, ClassFilter, AndFilter
from app.ml_pipe import ml_pipe, ml_parallel, ml_map, ml_run
from app.model import ModelClassification, ModelDetect
from app.transform import CropImage


def main():
    crop_image_tl = CropImage(x=1027, y=336, width=24, height=32)
    model_tl = ModelClassification(model_path='data/model/model-traffic-light.pt')
    class_filter_tl = ClassFilter(class_index=0)
    model_detect = ModelDetect(model_path='yolov8n.pt')
    filter_human = ObjectClassFilter(name='person')
    position_filter_human = ObjectPositionFilter(x1=760, y1=440, x2=920, y2=550)
    and_filter = AndFilter()
    send_message = ActionSendMessage()
    camera = Camera('data/demo.mp4')

    pipe_tl = ml_pipe(crop_image_tl, model_tl, class_filter_tl)
    pipe_human = ml_pipe(model_detect, filter_human, position_filter_human)
    pipe_detect = ml_pipe(ml_parallel(pipe_tl, pipe_human), and_filter, send_message)
    pipe_main = ml_map(camera, pipe_detect)
    ml_run(pipe_main)


main()
