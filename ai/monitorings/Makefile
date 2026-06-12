.PHONY: *

docker_init:
ifeq ($(OS),Windows_NT)
	echo "AIRFLOW_UID=50000"
else
	mkdir -p ./dags ./logs ./plugins ./config
	echo -e "AIRFLOW_UID=$(id -u)" > .env
endif

	docker compose up airflow-init

docker_up:
	docker compose up -d --build

docker_stop:
	docker compose stop

docker_clean_up_all_data:
	docker compose --profile "*" down --volumes --remove-orphans
