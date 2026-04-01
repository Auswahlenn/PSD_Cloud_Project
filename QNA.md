# Presentation Q&A Reference

## How did I build this system?

### Step 1 — Containerize the MQTT Broker
- Wrote a Dockerfile wrapping `eclipse-mosquitto` with a custom config
- Built the image and pushed it to **Google Artifact Registry**
- The MQTT broker runs as a Docker container on a **GCE VM** (not Kubernetes — it is a lightweight edge component)

### Step 2 — Provision All Cloud Infrastructure with Terraform
Ran `tofu apply` once to create everything:
- **GCE VM** for the MQTT broker
- **GKE cluster** (2 nodes, e2-medium) for all Kubernetes workloads
- **Artifact Registry** repository to store Docker images
- **Cloud Pub/Sub** topic and subscription
- **Cloud Dataflow** job using GCP's pre-built `Mqtt_to_PubSub` Flex Template — this bridges MQTT to Pub/Sub
- **IAM** service accounts and roles (least privilege)

### Step 3 — Build the gRPC Server
- Defined the API in a `.proto` file (Protocol Buffers)
- Compiled with `protoc` to generate Go code
- Wrote the Go server logic: pulls messages from Pub/Sub, parses JSON, inserts into PostgreSQL
- Built into a Docker image via multi-stage build and pushed to Artifact Registry

### Step 4 — Deploy Kubernetes Workloads
Applied K8s manifests in order:
1. `namespace.yaml` — create `iot` namespace
2. `secrets.yaml` — database credentials
3. CNPG operator — installed via `kubectl apply` from GitHub releases
4. `cnpg-cluster.yaml` — provisions a 2-node HA PostgreSQL cluster (primary + replica)
5. `grpc-server.yaml` — deploys the gRPC server with HPA (2–10 replicas, 60% CPU threshold)
6. `grafana.yaml` — deploys Grafana with LoadBalancer service

### Step 5 — Install Observability Stack
- Installed **Prometheus** via Helm (`kube-prometheus-stack`)
- Added Prometheus as a data source in Grafana
- Created dashboards for temperature time-series and Kubernetes metrics

---

## Common Q&A

**Q: Why MQTT and not HTTP/REST?**
MQTT is a lightweight publish-subscribe protocol designed for constrained IoT devices (low bandwidth, unreliable networks). HTTP adds too much overhead for devices like Jetson Nano or LoRaWAN gateways.

**Q: Why Dataflow instead of connecting directly to Pub/Sub?**
IoT devices speak MQTT — Pub/Sub does not natively understand MQTT. Dataflow acts as a bridge, handling protocol translation. It also provides a managed, scalable streaming layer.

**Q: Why Pub/Sub between Dataflow and gRPC?**
Pub/Sub decouples producers from consumers. If the gRPC server is temporarily down or scaling, messages are buffered in Pub/Sub and not lost. This ensures at-least-once delivery.

**Q: Why gRPC instead of REST?**
gRPC uses Protocol Buffers (binary) instead of JSON (text), which is faster and more efficient. It is strongly typed and auto-generates client/server code from `.proto` files.

**Q: Why CloudNativePG instead of a standalone PostgreSQL?**
CNPG manages a primary-replica PostgreSQL cluster with automatic failover. If the primary node crashes, the replica is promoted automatically with zero downtime. A standalone PostgreSQL is a single point of failure.

**Q: How does autoscaling work?**
Kubernetes Horizontal Pod Autoscaler (HPA) monitors CPU usage on the gRPC server pods. When CPU exceeds 60%, it adds more replicas (up to 10). When load drops, it scales back down after a cooldown period.

**Q: Why Terraform / Infrastructure as Code?**
IaC makes the entire infrastructure reproducible. Any team member can recreate the full environment with one command (`tofu apply`). It also prevents configuration drift and enables version-controlled infrastructure changes.

**Q: What happens if the MQTT broker VM goes down?**
Dataflow will lose its MQTT connection and stop forwarding messages. This is a known limitation — the VM is a single point of failure. A production improvement would be to run the MQTT broker as a clustered deployment (e.g., EMQX cluster) or use a managed MQTT service.

**Q: How is security handled?**
- IAM roles follow least privilege (e.g., Dataflow worker only has `pubsub.publisher`)
- Database credentials stored in Kubernetes Secrets, not hardcoded
- GKE nodes use a dedicated service account, not the default compute SA
- MQTT uses username/password authentication

**Q: What would you improve for production?**
1. Mutual TLS between services
2. MQTT broker cluster for HA
3. Custom HPA metrics (e.g., scale on Pub/Sub backlog depth, not just CPU)
4. Automated `terraform destroy` on a schedule to save costs
5. CI/CD pipeline for image builds and deployments
