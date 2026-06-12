IMAGE_TAG=1

docker build -t registry.m16.tech/docker-gitlab:$IMAGE_TAG .
docker push registry.m16.tech/docker-gitlab:$IMAGE_TAG