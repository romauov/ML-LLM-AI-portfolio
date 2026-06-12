"""
Подключение страниц на gradio

@author Sergey Goncharov
"""
import os

import gradio as gr
import sentry_sdk
from fastapi import FastAPI

# from product.gradio import gr_interface
from farm_model.gradio import gr_farm_interface
# from name_classifier.gradio import gr_surname_interface
from yolo_pit.gradio import gr_yolo_interface
from tracker.gradio import gr_tracker_interface
from answer_validator.gradio import gr_validator_interface
from knn_recommendations.gradio import gr_recommendation_interface
from bert_recommendations.gradio import gr_recommendation_bert_interface
from card_recommendation.gradio import gr_recommendation_card_interface
from cluster_recmndr.gradio import gradio_cluster_recommender_interface
from text_templater.gradio_v2 import gr_generation_interface_v2
from chat_helper.gradio import gr_chat_helper_interface
from forecasting.gradio import gr_forecasting_interface
from user_card.gradio import gr_user_card_interface
from msg_classifier.gradio import gr_msg_classifier_interface

if os.environ['MODE'] == 'PROD':
    sentry_sdk.init(
        dsn="http://{{SENTRY_DSN}}",
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=1.0,
    )

app = FastAPI()

# gr.mount_gradio_app(app, gr_interface(), path="/gradio/product")
gr.mount_gradio_app(app, gr_farm_interface(), path="/gradio/farm_model")
# gr.mount_gradio_app(app, gr_surname_interface(), path="/gradio/surname_classifier")
gr.mount_gradio_app(app, gr_yolo_interface(), path="/gradio/yolo")
gr.mount_gradio_app(app, gr_tracker_interface(), path="/gradio/tracker")
gr.mount_gradio_app(app, gr_validator_interface(), path="/gradio/answer_validator")
gr.mount_gradio_app(app, gr_validator_interface(), path="/gradio/answer_validator")
gr.mount_gradio_app(app, gr_recommendation_interface(), path="/gradio/knn_recommenations")
gr.mount_gradio_app(app, gr_recommendation_card_interface(), path="/gradio/card_interface")
gr.mount_gradio_app(app, gr_recommendation_bert_interface(), path="/gradio/bert_recommenations")
gr.mount_gradio_app(app, gradio_cluster_recommender_interface(), path="/gradio/cluster_recmndr")
gr.mount_gradio_app(app, gr_generation_interface_v2(), path='/gradio/text_generation_v2')
gr.mount_gradio_app(app, gr_chat_helper_interface(), path="/gradio/chat_helper")
gr.mount_gradio_app(app, gr_forecasting_interface(), path="/gradio/forecasting")
gr.mount_gradio_app(app, gr_user_card_interface(), path="/gradio/user_profile")
gr.mount_gradio_app(app, gr_msg_classifier_interface(), path="/gradio/msg_classifier")
