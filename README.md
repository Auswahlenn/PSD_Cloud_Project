# GCP IoT ESP — End-to-End Data Pipeline

IoT temperature sensor pipeline on GCP:
**MQTT Publisher → Mosquitto Broker (GCE) → Dataflow → Pub/Sub → gRPC Server (GKE) → PostgreSQL (CNPG) → Grafana**

## Architecture

```
fake_temperature_publisher.py
        │
        ▼
  MQTT Broker (GCE VM)
        │
        ▼
  Dataflow (Mqtt_to_PubSub flex template)
        │
        ▼
  Cloud Pub/Sub
        │
        ▼
  gRPC Server (GKE, autoscaled 2-10 pods)
        │
        ▼
  PostgreSQL (CNPG operator, 1 primary + 1 replica)
        │
        ▼
  Grafana Dashboard
```

## Infrastructure (Terraform)

Modules: `iam`, `mqtt_broker`, `pubsub`, `dataflow`, `gke`

```bash
# Authenticate
gcloud auth application-default login

# Deploy infrastructure
cd terraform
terraform plan
terraform apply
```

## MQTT Broker Docker Image

The broker runs on a GCE VM via Container-Optimized OS. Build and push the image:

```bash
# Multi-platform build (Macbook is arm64, VM is amd64)
docker buildx build --platform linux/amd64,linux/arm64 \
  -t us-central1-docker.pkg.dev/project-4a8f3b06-8ff8-4efd-a4d/mqtt-broker/mqtt_broker:latest \
  --push .
```

## Kubernetes Setup (Post Terraform)

After `terraform apply`, run these to deploy the K8s workloads:

```bash
# 1. Get GKE credentials
gcloud container clusters get-credentials iot-cluster --zone us-central1-a --project project-4a8f3b06-8ff8-4efd-a4d

# 2. Install CNPG operator
kubectl apply --server-side -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.25/releases/cnpg-1.25.1.yaml
kubectl -n cnpg-system rollout status deployment/cnpg-controller-manager --timeout=120s

# 3. Apply K8s manifests
kubectl apply -f timescaledb/k8s/namespace.yaml
kubectl apply -f timescaledb/k8s/secrets.yaml
kubectl apply -f timescaledb/k8s/cnpg-cluster.yaml
kubectl -n iot get cluster timescaledb-operator -w   # wait until READY=2

# 4. Run migration & set password
kubectl -n iot exec -i timescaledb-operator-1 -c postgres -- psql -U postgres -d temperatures -c "
CREATE TABLE IF NOT EXISTS temperatures (
    time TIMESTAMPTZ NOT NULL,
    device TEXT NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    unit TEXT NOT NULL DEFAULT 'C'
);
CREATE INDEX IF NOT EXISTS idx_temperatures_device_time ON temperatures (device, time DESC);
ALTER USER postgres WITH PASSWORD 'changeme-in-production';
"

# 5. Deploy gRPC server + Grafana
kubectl apply -f timescaledb/k8s/grpc-server.yaml
kubectl apply -f timescaledb/k8s/grafana.yaml

# 6. Install Prometheus for K8s monitoring
helm install kube-prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --set grafana.enabled=false \
  --set prometheus.prometheusSpec.resources.requests.cpu=50m \
  --set prometheus.prometheusSpec.resources.requests.memory=128Mi \
  --set prometheus.prometheusSpec.resources.limits.cpu=500m \
  --set prometheus.prometheusSpec.resources.limits.memory=512Mi \
  --set prometheus.prometheusSpec.retention=3d \
  --set alertmanager.enabled=false
```

## Fake Temperature Publisher

Simulates IoT sensors publishing to the MQTT broker:

```bash
# Single sensor
python fake_temperature_publisher.py --host <MQTT_BROKER_IP>

# 10 sensors, 2 second interval
python fake_temperature_publisher.py --host <MQTT_BROKER_IP> --sensors 10 --interval 2
```

## Useful Commands

```bash
# Check pods
kubectl -n iot get pods

# Check CNPG cluster health
kubectl -n iot get cluster timescaledb-operator

# Query database
kubectl -n iot exec -i timescaledb-operator-1 -c postgres -- psql -U postgres -d temperatures -c "SELECT * FROM temperatures ORDER BY time DESC LIMIT 5;"

# gRPC server logs
kubectl -n iot logs -l app=grpc-server --tail=20

# Grafana external IP
kubectl -n iot get svc grafana

# Dataflow jobs
gcloud dataflow jobs list --region=us-central1 --project=project-4a8f3b06-8ff8-4efd-a4d --limit=5

# Cancel a Dataflow job
gcloud dataflow jobs cancel <JOB_ID> --region=us-central1 --project=project-4a8f3b06-8ff8-4efd-a4d

# Pub/Sub pull messages
gcloud pubsub subscriptions pull mqtt-broker-subscription --project=project-4a8f3b06-8ff8-4efd-a4d --auto-ack --limit=10

# Subscribe to MQTT broker locally
docker exec -it <CONTAINER_ID> mosquitto_sub -h localhost -t mqtt-broker-topic
```

## Tear Down

```bash
cd terraform
terraform destroy
```

Note: Terraform destroys all infra including Dataflow. Stop Dataflow manually in the GCP console first if you want to avoid recreating it on next `terraform apply`.
