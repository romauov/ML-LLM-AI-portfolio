FROM apache/airflow:latest-python3.10

WORKDIR /apps

RUN pip install clickhouse-driver mysql-connector-python==8.0.29 pandas==2.1.3 transformers==4.29.2 torch==1.11.0 numpy==1.24.3 pyarrow==11.0.0 polars faiss-cpu scikit-learn

USER root
RUN mkdir /home/user && chown -R 1000:1000 /home/user
RUN mkdir /home/user/.cache && chown -R 1000:1000 /home/user/.cache
