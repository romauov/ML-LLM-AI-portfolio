IMAGE_TAG=2

docker build -t registry.m16.tech/ansible:$IMAGE_TAG .
docker push registry.m16.tech/ansible:$IMAGE_TAG