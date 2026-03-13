gcloud auth application-default login

Terraform plan
Terraform apply

docker build -t mqtt_broker .
docker tag mqtt_broker us-central1-docker.pkg.dev/project-4a8f3b06-8ff8-4efd-a4d/mqtt-broker/mqtt_broker:latest
docker push us-central1-docker.pkg.dev/project-4a8f3b06-8ff8-4efd-a4d/mqtt-broker/mqtt_broker:latest

docker image need to be compaitable. Macbook is arm64, vm is amd64


docker buildx build --platform linux/amd64 \
  -t us-central1-docker.pkg.dev/project-4a8f3b06-8ff8-4efd-a4d/mqtt-broker/mqtt_broker:latest \
  --push .

docker buildx build --platform linux/amd64,linux/arm64 \
  -t us-central1-docker.pkg.dev/project-4a8f3b06-8ff8-4efd-a4d/mqtt-broker/mqtt_broker:latest \
  --push .

docker buildx imagetools inspect us-central1-docker.pkg.dev/project-4a8f3b06-8ff8-4efd-a4d/mqtt-broker/mqtt_broker:latest

gcloud dataflow flex-template run mqtt-to-pubsub-$(date +%m%d-%H%M%S) --project=project-4a8f3b06-8ff8-4efd-a4d --region=us-central1 --enable-streaming-engine --template-file-gcs-location=gs://dataflow-templates-us-central1/latest/flex/Mqtt_to_PubSub --parameters brokerServer=tcp://34.61.243.83:1883,inputTopic=mqtt-broker-topic,outputTopic=projects/project-4a8f3b06-8ff8-4efd-a4d/topics/mqtt-broker-topic,username=guest,password=guest

docker exec -it 18a220b72552 mosquitto_sub -h localhost -t mqtt-broker-topic

gcloud dataflow jobs list --region=us-central1 --project=project-4a8f3b06-8ff8-4efd-a4d --limit=5

gcloud dataflow jobs cancel <ID> --region=us-central1 --project=project-4a8f3b06-8ff8-4efd-a4d
