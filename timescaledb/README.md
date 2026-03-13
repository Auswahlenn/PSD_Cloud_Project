protoc --go_out=. --go-grpc_out=. protoc/temperature.proto
go mod tidy 
docker buildx build --platform linux/amd64 \
  -t us-central1-docker.pkg.dev/project-4a8f3b06-8ff8-4efd-a4d/mqtt-broker/grpc-server:latest \
  --push .

  gcloud container clusters get-credentials iot-cluster --zone=us-central1-a --project=project-4a8f3b06-8ff8-4efd-a4d

cd /Users/pangjiade/Documents/GitHub/GCP-ESP/timescaledb

kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/timescaledb.yaml

# Wait for TimescaleDB to be ready
kubectl -n iot wait --for=condition=ready pod -l app=timescaledb --timeout=120s

# Run the migration
kubectl -n iot exec -it statefulset/timescaledb -- psql -U postgres -d temperatures -f /dev/stdin < migrations/001_create_temperatures.sql

# Deploy gRPC server and Grafana
kubectl apply -f k8s/grpc-server.yaml
kubectl apply -f k8s/grafana.yaml

# Connect to cluster
gcloud container clusters get-credentials iot-cluster --zone=us-central1-a --project=project-4a8f3b06-8ff8-4efd-a4d

gcloud components install gke-gcloud-auth-plugin

cd /Users/pangjiade/Documents/GitHub/GCP-ESP/timescaledb

# Namespace and secrets
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml

# TimescaleDB
kubectl apply -f k8s/timescaledb.yaml
kubectl -n iot wait --for=condition=ready pod -l app=timescaledb --timeout=120s

# Run migration
kubectl -n iot exec -it statefulset/timescaledb -- psql -U postgres -d temperatures -f /dev/stdin < migrations/001_create_temperatures.sql

# gRPC server and Grafana
kubectl apply -f k8s/grpc-server.yaml
kubectl apply -f k8s/grafana.yaml

kubectl -n iot get pods
kubectl -n iot get svc grafana
kubectl -n iot logs -l app=grpc-server --tail=20

kubectl -n iot exec -i timescaledb-operator-1 -c postgres -- psql -U postgres -d temperatures -c "SELECT * FROM temperatures ORDER BY time DESC LIMIT 5;" 2>&1



Grafana setup
Open Grafana: http://34.45.145.181 (login: admin / admin)

Add PostgreSQL data source:

Go to Connections > Data sources > Add data source > PostgreSQL
Settings:
Host: timescaledb-operator-rw.iot.svc.cluster.local:5432
Database: temperatures
User: postgres
Password: changeme-in-production
TLS/SSL Mode: disable
Click Save & Test
Create a dashboard — go to Dashboards > New > New Dashboard > Add visualization, select the PostgreSQL data source, then use these queries:

Temperature over time (line chart):


SELECT
  time AS "time",
  device,
  value
FROM temperatures
WHERE $__timeFilter(time)
ORDER BY time
Latest reading per sensor (table):


SELECT DISTINCT ON (device)
  device,
  value,
  unit,
  time
FROM temperatures
ORDER BY device, time DESC
Average temperature per sensor (bar chart):


SELECT
  device,
  AVG(value) as avg_temp
FROM temperatures
WHERE $__timeFilter(time)
GROUP BY device
ORDER BY device
The $__timeFilter(time) macro is Grafana's built-in — it automatically filters by the time range you select in the dashboard's time picker (top right).