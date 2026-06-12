IMAGE_TAG=3

docker build -t registry.m16.tech/ml-lib:$IMAGE_TAG .
docker push registry.m16.tech/ml-lib:$IMAGE_TAG
