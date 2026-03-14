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

## Prerequisites

- [Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/docs/install)
- [Terraform](https://developer.hashicorp.com/terraform/install)
- [Docker](https://docs.docker.com/get-docker/) with `buildx` support
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [Helm](https://helm.sh/docs/intro/install/)
- [gke-gcloud-auth-plugin](https://cloud.google.com/kubernetes-engine/docs/how-to/cluster-access-for-kubectl#install_plugin): `gcloud components install gke-gcloud-auth-plugin`
- Python 3 with `paho-mqtt`: `pip install paho-mqtt`

## Step 1: Deploy Infrastructure (Terraform)

Terraform manages 5 modules: `iam`, `mqtt_broker`, `pubsub`, `dataflow`, `gke`

```bash
# Authenticate with GCP
gcloud auth application-default login

# Deploy all infrastructure
cd terraform
terraform init
terraform plan
terraform apply
```

> **Note:** The Dataflow job may fail on first apply if the MQTT broker isn't fully ready yet. This is expected — you can re-run it later from the GCP console or with `terraform apply` again.

After apply, note the MQTT broker IP:

```bash
terraform output mqtt_broker_external_ip
```

## Step 2: Build & Push Docker Images

### MQTT Broker

```bash
# From the docker-file/ directory
cd docker-file
docker buildx build --platform linux/amd64,linux/arm64 \
  -t us-central1-docker.pkg.dev/project-4a8f3b06-8ff8-4efd-a4d/mqtt-broker/mqtt_broker:latest \
  --push .
```

### gRPC Server

```bash
# From the timescaledb/ directory
cd timescaledb
protoc --go_out=. --go-grpc_out=. protoc/temperature.proto
go mod tidy
docker buildx build --platform linux/amd64 \
  -t us-central1-docker.pkg.dev/project-4a8f3b06-8ff8-4efd-a4d/mqtt-broker/grpc-server:latest \
  --push .
```

## Step 3: Deploy Kubernetes Workloads

After `terraform apply` completes and the GKE cluster is ready:

```bash
# 1. Get GKE credentials
gcloud container clusters get-credentials iot-cluster \
  --zone us-central1-a \
  --project project-4a8f3b06-8ff8-4efd-a4d

# 2. Install CloudNativePG (CNPG) operator
kubectl apply --server-side \
  -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.25/releases/cnpg-1.25.1.yaml
kubectl -n cnpg-system rollout status deployment/cnpg-controller-manager --timeout=120s

# 3. Create namespace, secrets, and CNPG PostgreSQL cluster
kubectl apply -f timescaledb/k8s/namespace.yaml
kubectl apply -f timescaledb/k8s/secrets.yaml
kubectl apply -f timescaledb/k8s/cnpg-cluster.yaml

# 4. Wait for CNPG cluster to be healthy (READY should show 2)
kubectl -n iot get cluster timescaledb-operator -w
```

Once the cluster shows `READY=2` and `Cluster in healthy state`:

```bash
# 5. Run database migration and set password
kubectl -n iot exec -i timescaledb-operator-1 -c postgres -- \
  psql -U postgres -d temperatures -c "
CREATE TABLE IF NOT EXISTS temperatures (
    time TIMESTAMPTZ NOT NULL,
    device TEXT NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    unit TEXT NOT NULL DEFAULT 'C'
);
CREATE INDEX IF NOT EXISTS idx_temperatures_device_time ON temperatures (device, time DESC);
ALTER USER postgres WITH PASSWORD 'changeme-in-production';
"

# 6. Deploy gRPC server and Grafana
kubectl apply -f timescaledb/k8s/grpc-server.yaml
kubectl apply -f timescaledb/k8s/grafana.yaml

# 7. Install Prometheus for Kubernetes monitoring
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
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

## Step 4: Verify Everything is Running

```bash
# Check all pods are running
kubectl -n iot get pods

# Check CNPG cluster health
kubectl -n iot get cluster timescaledb-operator

# Get Grafana external IP
kubectl -n iot get svc grafana

# Check gRPC server logs (should show "stored: device=..." messages)
kubectl -n iot logs -l app=grpc-server --tail=20

# Query the database directly
kubectl -n iot exec -i timescaledb-operator-1 -c postgres -- \
  psql -U postgres -d temperatures -c "SELECT * FROM temperatures ORDER BY time DESC LIMIT 5;"
```

## Step 5: Run the Fake Temperature Publisher

Update the `--host` flag with the MQTT broker IP from Step 1:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install paho-mqtt

# Single sensor
python fake_temperature_publisher.py --host <MQTT_BROKER_IP>

# 10 sensors, 2 second interval
python fake_temperature_publisher.py --host <MQTT_BROKER_IP> --sensors 10 --interval 2
```

## Step 6: Configure Grafana

1. Open Grafana at `http://<GRAFANA_EXTERNAL_IP>` (login: `admin` / `admin`)

2. **Add PostgreSQL data source** (Connections > Data sources > PostgreSQL):
   - Host: `timescaledb-operator-rw.iot.svc.cluster.local:5432`
   - Database: `temperatures`
   - User: `postgres`
   - Password: `changeme-in-production`
   - TLS/SSL Mode: `disable`

3. **Add Prometheus data source** (Connections > Data sources > Prometheus):
   - URL: `http://kube-prometheus-kube-prome-prometheus.monitoring.svc.cluster.local:9090`

4. **Create temperature dashboard** (Dashboards > New > Add visualization):
   - Visualization: **Time series**
   - Query (Code mode):
     ```sql
     SELECT
       $__timeGroup(time, '5s') AS "time",
       device,
       AVG(value) AS value
     FROM temperatures
     WHERE $__timeFilter(time)
     GROUP BY 1, device
     ORDER BY 1
     ```
   - Format as: **Time series**
   - Each sensor appears as a separate colored line

5. **Import Kubernetes monitoring dashboards** (Dashboards > Import):
   - `15760` — Kubernetes cluster overview
   - `15757` — Kubernetes pods monitoring
   - `1860` — Node Exporter Full

## Useful Commands

```bash
# Dataflow jobs
gcloud dataflow jobs list --region=us-central1 --project=project-4a8f3b06-8ff8-4efd-a4d --limit=5

# Cancel a Dataflow job
gcloud dataflow jobs cancel <JOB_ID> --region=us-central1 --project=project-4a8f3b06-8ff8-4efd-a4d

# Pub/Sub pull messages
gcloud pubsub subscriptions pull mqtt-broker-subscription \
  --project=project-4a8f3b06-8ff8-4efd-a4d --auto-ack --limit=10

# Subscribe to MQTT broker locally
docker exec -it <CONTAINER_ID> mosquitto_sub -h localhost -t mqtt-broker-topic
```

## Tear Down

```bash
cd terraform
terraform destroy
```

> **Note:** Terraform destroys all infrastructure including the Dataflow job. If you want to avoid Dataflow being recreated on next `terraform apply`, stop it manually in the GCP console first.
