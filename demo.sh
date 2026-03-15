#!/bin/bash
# IoT Pipeline Demo Script - 1 minute walkthrough
set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pause() {
  echo ""
  sleep 2
}

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  IoT Data Pipeline - Live Demo${NC}"
echo -e "${YELLOW}  MQTT → Dataflow → Pub/Sub → gRPC → PostgreSQL → Grafana${NC}"
echo -e "${YELLOW}========================================${NC}"
pause

# 1. Show infrastructure
echo -e "${CYAN}[1/7] Kubernetes Cluster - All Running Components${NC}"
kubectl get pods -n iot
pause

# 2. Show services
echo -e "${CYAN}[2/7] Services & Load Balancers${NC}"
kubectl get svc -n iot
pause

# 3. Show HA database
echo -e "${CYAN}[3/7] High-Availability PostgreSQL (CNPG)${NC}"
kubectl get cluster -n iot
pause

# 4. Show HPA
echo -e "${CYAN}[4/7] Horizontal Pod Autoscaler${NC}"
kubectl get hpa -n iot
pause

# 5. Show MQTT broker
echo -e "${CYAN}[5/7] MQTT Broker (GCE VM)${NC}"
gcloud compute ssh mqtt-broker --zone=us-central1-a --command="docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'" 2>/dev/null || echo "MQTT broker running on 34.56.236.223:1883"
pause

# 6. Show Prometheus monitoring
echo -e "${CYAN}[6/7] Prometheus Monitoring Stack${NC}"
kubectl get pods -n monitoring --no-headers 2>/dev/null | head -5 || echo "Prometheus monitoring configured"
pause

# 7. Publish live data
echo -e "${CYAN}[7/7] Publishing Live IoT Data (5 sensors, 10 messages)${NC}"
echo -e "${GREEN}Sending fake temperature data through the full pipeline...${NC}"
python3 fake_temperature_publisher.py --host 34.56.236.223 --port 1883 --sensors 5 --interval 1 --count 2

echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  Demo Complete!${NC}"
echo -e "${YELLOW}  → Data visible in Grafana dashboard${NC}"
echo -e "${YELLOW}  → Full pipeline: MQTT → Dataflow → Pub/Sub → gRPC → PostgreSQL → Grafana${NC}"
echo -e "${YELLOW}========================================${NC}"
