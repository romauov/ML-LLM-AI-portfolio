# Makefile для запуска тестов
# Работает на Windows, Linux и macOS
include .env
export


ifeq ($(OS),Windows_NT)
    VENV_DIR = venv
    PYTHON = $(VENV_DIR)\Scripts\python
else
    VENV_DIR = venv
    PYTHON = $(VENV_DIR)/bin/python
endif

.PHONY: unit-tests api-tests e2e-tests

unit-tests:
	$(PYTHON) -W ignore -m pytest tests/unit/models/ tests/unit/data/ -v

api-tests:
	$(PYTHON) -W ignore -m pytest tests/api/api_tests.py -v

e2e-tests:
	$(PYTHON) -W ignore -m pytest tests/e2e -v

download_hf_models:
	$(PYTHON) -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='google/timesfm-2.5-200m-pytorch', filename='config.json', cache_dir='storage/.cache/huggingface', token='$(HF_TOKEN)')"
	$(PYTHON) -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='google/timesfm-2.5-200m-pytorch', filename='model.safetensors', cache_dir='storage/.cache/huggingface', token='$(HF_TOKEN)')"

