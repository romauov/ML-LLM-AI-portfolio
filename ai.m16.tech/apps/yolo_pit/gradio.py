"""
Интерфейс для модели

@author Dmitry Abramov
"""
import gradio as gr
from ultralytics import YOLO
from PIL import Image

def predict(img) -> str:
    """
    Детекция изображения 
    :params: 
        img - загруженное изображение
    :return:
        путь к результату детекции
    """
    model = YOLO('apps/yolo_pit/data/model.pt')
    results = model(img)
    img = results[0].plot()
    return Image.fromarray(img)

def gr_yolo_interface():
    """
    Интерфейс для модели Yolo
    """
    return gr.Interface(fn=predict,
                        title='YOLOv8 прототип',
                        inputs=gr.Image(),
                        outputs=gr.Image(shape=(640, 640)),
                        examples=['apps/yolo_pit/data/images/examples/1.jpeg',
                                  'apps/yolo_pit/data/images/examples/2.png'])
