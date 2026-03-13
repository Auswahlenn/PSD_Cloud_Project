# Cloud & Cloud-Native Capabilities

## Cloud Services (GCP)

| Service | Purpose | Why Cloud-Native |
|---------|---------|------------------|
| **Google Kubernetes Engine (GKE)** | Container orchestration for gRPC server, PostgreSQL, Grafana | Managed Kubernetes — no control plane maintenance, auto-repair, integrated with GCP IAM |
| **Cloud Dataflow** | Streaming ETL from MQTT to Pub/Sub | Fully managed, serverless, auto-scaling Apache Beam runner — no infrastructure to provision |
| **Cloud Pub/Sub** | Message queue between Dataflow and gRPC server | Fully managed message broker with at-least-once delivery, decouples producers from consumers |
| **Compute Engine** | Hosts MQTT broker (Mosquitto) via Container-Optimized OS | VM with container runtime — bridges legacy IoT protocol (MQTT) into cloud-native pipeline |
| **Artifact Registry** | Docker image storage for MQTT broker and gRPC server | Managed container registry integrated with GKE image pulling and IAM access control |
| **Cloud IAM** | Service accounts and role-based access | Principle of least privilege — each component has only the permissions it needs |

## Cloud-Native Patterns

### 1. Infrastructure as Code (IaC)
- **Terraform** manages all GCP resources declaratively across 5 modules (`iam`, `mqtt_broker`, `pubsub`, `dataflow`, `gke`)
- Reproducible deployments: `terraform destroy` and `terraform apply` recreates the entire infrastructure identically
- State management via `terraform.tfstate` tracks resource lifecycle

### 2. Containerization
- **gRPC server**: Multi-stage Docker build (Go compile → minimal runtime image) reduces image size and attack surface
- **MQTT broker**: Runs on Container-Optimized OS on GCE, pulled from Artifact Registry
- **All K8s workloads** run as containers — Grafana, PostgreSQL, Prometheus, gRPC server

### 3. Container Orchestration (Kubernetes)
- **Deployments** for stateless workloads (gRPC server, Grafana) with rolling updates and rollback
- **Namespaces** for logical isolation (`iot` for application, `monitoring` for observability, `cnpg-system` for database operator)
- **Services** for internal service discovery (ClusterIP) and external access (LoadBalancer)
- **Secrets** for sensitive configuration (database passwords, Grafana credentials)
- **Resource requests and limits** on all pods to ensure fair scheduling and prevent noisy neighbors

### 4. Horizontal Pod Autoscaling (HPA)
- gRPC server scales from **2 to 10 replicas** based on CPU utilization (60% threshold)
- Kubernetes automatically adds/removes pods in response to load from IoT sensors
- Ensures the system handles traffic spikes without manual intervention

### 5. High Availability (HA) — CloudNativePG Operator
- **CNPG operator** manages PostgreSQL with **1 primary + 1 replica** (streaming replication)
- **Automatic failover**: if the primary pod crashes, the replica promotes to primary within seconds
- **Self-healing**: operator detects and replaces failed instances automatically
- **Three service endpoints**: `rw` (writes to primary), `ro` (reads from replicas), `r` (any instance) — enables read/write splitting

### 6. Event-Driven / Asynchronous Messaging
- **Pub/Sub** decouples data ingestion (Dataflow) from data processing (gRPC server)
- Subscribers process messages at their own pace — Pub/Sub buffers during traffic spikes
- At-least-once delivery guarantees no data loss
- Subscription-based model allows adding new consumers without modifying producers

### 7. Streaming Data Pipeline
- **Dataflow** processes MQTT messages in real-time (not batch) using streaming mode
- End-to-end latency from sensor publish to database insert is seconds, not minutes
- Dataflow auto-scales workers based on backlog — handles variable IoT sensor throughput

### 8. Observability
- **Grafana** provides unified dashboards for both application data and infrastructure metrics
- **Prometheus** (kube-prometheus-stack) collects Kubernetes metrics: CPU, memory, pod health, node status
- **Node Exporter** provides host-level metrics (disk, network, system load)
- **kube-state-metrics** exposes Kubernetes object states (deployment replicas, pod phases, HPA status)

### 9. Microservices Architecture
- Each component has a single responsibility:
  - `fake_temperature_publisher.py` — data generation
  - Mosquitto broker — MQTT protocol handling
  - Dataflow — protocol bridging (MQTT → Pub/Sub)
  - Pub/Sub — message buffering
  - gRPC server — data ingestion and API serving
  - PostgreSQL (CNPG) — persistent storage
  - Grafana — visualization
- Components communicate over well-defined interfaces (MQTT, Pub/Sub, gRPC, SQL)
- Each service can be scaled, updated, or replaced independently

### 10. Protocol Bridging
- IoT devices speak **MQTT** (lightweight, designed for constrained devices)
- Cloud services use **Pub/Sub** (managed, scalable, integrated with GCP)
- **Dataflow** bridges these two worlds — no custom code needed (uses Google's flex template)
- Internal services communicate via **gRPC** (efficient binary protocol with protobuf schema)

## Security Practices

| Practice | Implementation |
|----------|---------------|
| **Least privilege IAM** | Separate service accounts with specific roles (`dataflow.worker`, `pubsub.publisher`, `pubsub.subscriber`, `artifactregistry.reader`) |
| **Secrets management** | Kubernetes Secrets for database passwords — not hardcoded in manifests or code |
| **Network isolation** | ClusterIP services for internal communication — only Grafana exposed via LoadBalancer |
| **Container security** | Multi-stage Docker builds minimize attack surface; no root processes |

## Scalability Summary

| Component | Scaling Method | Details |
|-----------|---------------|---------|
| MQTT Broker | Vertical (VM resize) | Single Mosquitto instance on GCE |
| Dataflow | Auto (managed) | Workers scale based on message backlog |
| Pub/Sub | Auto (managed) | Fully managed, scales transparently |
| gRPC Server | Horizontal (HPA) | 2-10 pods, CPU-based autoscaling |
| PostgreSQL | Operator-managed | CNPG handles replica creation, failover |
| Prometheus | Vertical | Single instance with retention policy |
| Grafana | Vertical | Single instance, stateless |
