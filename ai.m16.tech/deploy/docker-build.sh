#! /bin/bash

# Создание докер образа ml-services-python

echo "{{INTERNAL_IP}}    registry.m16.tech" >> /etc/hosts

# Получить из файла .env версию образа
export $(grep -v '^#' .env | xargs)

URL_REGISTRY="https://$DOCKER_REGISTRY_HOST/v2/"
URL_IMAGE_TAG="https://$DOCKER_REGISTRY_HOST/v2/ml-services-python/manifests/$ML_SERVICES_PYTHON_IMAGE_TAG"

function docker_registry_check() {
    curl --silent -f -lSL -u "$DOCKER_REGISTRY_USER:$DOCKER_REGISTRY_PASS" $URL_REGISTRY > /dev/null
}

function docker_tag_exists() {
    curl --silent -f -lSL -u "$DOCKER_REGISTRY_USER:$DOCKER_REGISTRY_PASS" $URL_IMAGE_TAG > /dev/null
}

# Проверка доступности docker registry
if docker_registry_check; then
  echo "ok"
else
  echo "docker registry не доступен"
  exit 1
fi

# Проверка версии образа в registry
if docker_tag_exists; then
    echo "docker образ с тегом $ML_SERVICES_PYTHON_IMAGE_TAG уже существует"
    exit 1
else
    echo "$DOCKER_REGISTRY_PASS" | docker login $DOCKER_REGISTRY_HOST --username $DOCKER_REGISTRY_USER --password-stdin
    docker build -t $DOCKER_REGISTRY_HOST/ml-services-python:$ML_SERVICES_PYTHON_IMAGE_TAG .
    docker build -t $DOCKER_REGISTRY_HOST/ml-services-python:latest .
    docker push $DOCKER_REGISTRY_HOST/ml-services-python:$ML_SERVICES_PYTHON_IMAGE_TAG
    docker push $DOCKER_REGISTRY_HOST/ml-services-python:latest
fi
