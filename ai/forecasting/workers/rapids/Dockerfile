FROM condaforge/miniforge3:26.1.0-0

ENV CONDA_PREFIX=/opt/conda

COPY conda-environment.yml /tmp/
RUN conda env update -n base -f /tmp/conda-environment.yml && \
    conda clean --all --yes && \
    rm /tmp/conda-environment.yml

RUN useradd -m -s /bin/bash appuser && \
    mkdir -p /home/appuser/app/storage && \
    chown -R appuser:appuser /home/appuser

USER appuser

WORKDIR /home/appuser/app

COPY --chown=appuser:appuser app app
COPY --chown=appuser:appuser worker.py .

CMD ["python", "-m", "worker"]
