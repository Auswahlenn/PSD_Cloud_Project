# TimescaleDB / gRPC Server

gRPC server in Go that subscribes to Pub/Sub, stores temperature data in PostgreSQL (CNPG operator), and serves queries via gRPC.

## Project Structure

```
timescaledb/
├── cmd/server/main.go          # Entrypoint: starts Pub/Sub subscriber + gRPC server
├── internal/
│   ├── db/db.go                # PostgreSQL query layer (insert, get, get latest)
│   ├── grpc/server.go          # gRPC handler implementation
│   └── subscriber/subscriber.go # Pub/Sub subscriber → DB insert
├── protoc/temperature.proto    # gRPC service definition
├── pb/                         # Generated protobuf Go code
├── migrations/
│   └── 001_create_temperatures.sql
├── k8s/
│   ├── namespace.yaml          # iot namespace
│   ├── secrets.yaml            # DB + Grafana passwords
│   ├── cnpg-cluster.yaml       # CNPG PostgreSQL HA cluster (1 primary + 1 replica)
│   ├── grpc-server.yaml        # Deployment + Service + HPA (2-10 replicas)
│   └── grafana.yaml            # Grafana deployment + LoadBalancer service
├── Dockerfile                  # Multi-stage Go build
├── go.mod
└── go.sum
```

## Build & Push Docker Image

```bash
# Generate protobuf code
protoc --go_out=. --go-grpc_out=. protoc/temperature.proto
go mod tidy

# Build and push (amd64 for GKE)
docker buildx build --platform linux/amd64 \
  -t us-central1-docker.pkg.dev/project-4a8f3b06-8ff8-4efd-a4d/mqtt-broker/grpc-server:latest \
  --push .
```

## Deploy to GKE

```bash
# Get cluster credentials
gcloud container clusters get-credentials iot-cluster --zone=us-central1-a --project=project-4a8f3b06-8ff8-4efd-a4d

# Install CNPG operator
kubectl apply --server-side -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.25/releases/cnpg-1.25.1.yaml
kubectl -n cnpg-system rollout status deployment/cnpg-controller-manager --timeout=120s

# Deploy namespace, secrets, CNPG cluster
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/cnpg-cluster.yaml
kubectl -n iot get cluster timescaledb-operator -w   # wait until READY=2

# Run migration & set password
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

# Deploy gRPC server + Grafana
kubectl apply -f k8s/grpc-server.yaml
kubectl apply -f k8s/grafana.yaml
```

## CNPG Services

| Service | Endpoint | Purpose |
|---------|----------|---------|
| `timescaledb-operator-rw` | Primary (read-write) | gRPC server writes here |
| `timescaledb-operator-ro` | Replicas (read-only) | Grafana reads here |
| `timescaledb-operator-r`  | Any instance | General reads |

## Useful Commands

```bash
# Check pods
kubectl -n iot get pods

# CNPG cluster health
kubectl -n iot get cluster timescaledb-operator

# Query database
kubectl -n iot exec -i timescaledb-operator-1 -c postgres -- psql -U postgres -d temperatures -c "SELECT * FROM temperatures ORDER BY time DESC LIMIT 5;"

# gRPC server logs
kubectl -n iot logs -l app=grpc-server --tail=20

# Grafana external IP
kubectl -n iot get svc grafana
```

## Grafana Setup

1. Open Grafana at `http://<GRAFANA_EXTERNAL_IP>` (login: `admin` / `admin`)
2. Add **PostgreSQL** data source:
   - Host: `timescaledb-operator-rw.iot.svc.cluster.local:5432`
   - Database: `temperatures`
   - User: `postgres`
   - Password: `changeme-in-production`
   - TLS/SSL Mode: `disable`
3. Add **Prometheus** data source (for K8s monitoring):
   - URL: `http://kube-prometheus-kube-prome-prometheus.monitoring.svc.cluster.local:9090`

### Dashboard Queries

**Temperature over time (Time series, one line per sensor):**
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

**Latest reading per sensor (Table):**
```sql
SELECT DISTINCT ON (device)
  device,
  value,
  unit,
  time
FROM temperatures
ORDER BY device, time DESC
```

**Average temperature per sensor (Bar chart):**
```sql
SELECT
  device,
  AVG(value) as avg_temp
FROM temperatures
WHERE $__timeFilter(time)
GROUP BY device
ORDER BY device
```

### K8s Monitoring Dashboards

Import these from grafana.com (Dashboards > Import > enter ID):
- **15760** — Kubernetes cluster overview
- **15757** — Kubernetes pods monitoring
- **1860** — Node Exporter Full
