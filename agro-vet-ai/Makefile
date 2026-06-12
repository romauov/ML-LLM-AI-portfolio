# Makefile для запуска API тестов Agro-Vet AI
# Совместим с Windows, Linux и macOS

.PHONY: test-api

# Установка значений по умолчанию для разных платформ
ifeq ($(OS),Windows_NT)
    PYTHON ?= python
    PYTEST ?= python -m pytest
else
    PYTHON ?= python3
    PYTEST ?= pytest
endif

# Запуск API тестов
test-api:
	$(PYTEST) tests/pytest/api/ -v