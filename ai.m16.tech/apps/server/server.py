"""
Веб-сервис для ML-моделей

команды:
python app/server.py     - production режим
python app/server.py dev - режим разработки

@author Sergey Goncharov
"""
import os
import sys

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from flask import Flask
from gevent.pywsgi import WSGIServer

from demo import blueprint as demo_blueprint
# from name_classifier import name_blueprint as name_classifier_blueprint
# from name_classifier import surname_blueprint as surname_classifier_blueprint
from cnn_based_driver_gaze_predictor import blueprint as cnn_based_driver_gaze_predictor_blueprint
# from product import blueprint as product_blueprint
# from mediapipe_based_head_controller import blueprint as mediapipe_based_head_controller
from server.middleware.prefix import PrefixMiddleware
# from buyers_definition import blueprint as buyers_definition_blueprint
# from weight_interest_algorithm import blueprint as weight_interest_blueprint
# from digital_sales_department import blueprint as digital_sales_department_blueprint
from tracker import blueprint as tracker_blueprint
from answer_validator import blueprint as validator_blueprint
# from leads_classification import blueprint as leads_classification_blueprint
from knn_recommendations import blueprint as knn_recommendations_blueprint
from text_templater import blueprint as text_templater_blueprint
from knn_recommendations_polars import blueprint as knn_recommendations_polars_blueprint
from digital_user_cards import blueprint as digital_user_cards_blueprint
from bert_recommendations import blueprint as bert_recommendations_blueprint
from cluster_recmndr import blueprint as cluster_recmndr_blueprint
from chat_helper import blueprint as chat_helper_blueprint
from saiga_chat import blueprint as saiga_chat_blueprint
from user_card import blueprint as user_card_blueprint
from msg_classifier import blueprint as msg_classifier_blueprint
from card_recommendation import blueprint as card_recommendation_blueprint


if os.environ['MODE'] == 'PROD':
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN', ''),
        integrations=[
            FlaskIntegration(),
        ],
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=1.0,
    )

app = Flask(__name__)

app.register_blueprint(demo_blueprint)
# app.register_blueprint(name_classifier_blueprint)
# app.register_blueprint(surname_classifier_blueprint)
app.register_blueprint(cnn_based_driver_gaze_predictor_blueprint)
# app.register_blueprint(product_blueprint)
# app.register_blueprint(mediapipe_based_head_controller)
# app.register_blueprint(buyers_definition_blueprint)
# app.register_blueprint(weight_interest_blueprint)
# app.register_blueprint(digital_sales_department_blueprint)
app.register_blueprint(tracker_blueprint)
app.register_blueprint(validator_blueprint)
# app.register_blueprint(leads_classification_blueprint)
app.register_blueprint(knn_recommendations_blueprint)
app.register_blueprint(text_templater_blueprint)
app.register_blueprint(knn_recommendations_polars_blueprint)
app.register_blueprint(digital_user_cards_blueprint)
app.register_blueprint(bert_recommendations_blueprint)
app.register_blueprint(cluster_recmndr_blueprint)
app.register_blueprint(chat_helper_blueprint)
app.register_blueprint(saiga_chat_blueprint)
app.register_blueprint(user_card_blueprint)
app.register_blueprint(msg_classifier_blueprint)
app.register_blueprint(card_recommendation_blueprint)

app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix='/api')

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'dev':
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        # Serve the app with gevent
        http_server = WSGIServer(('0.0.0.0', 5000), app)
        http_server.serve_forever()
