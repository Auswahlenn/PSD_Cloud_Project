#!/bin/sh

echo "Deployment script"

echo "🕝 namespace"
kubectl apply -f namespace.yaml
echo "✅ namespace"

echo "🕝 secrets"
kubectl apply -f secrets.yaml
echo "✅ secrets"

echo "🕝 cnpg operator"
if ! kubectl get crd clusters.postgresql.cnpg.io > /dev/null 2>&1; then
  echo "CRD not found, installing CNPG operator"
  kubectl apply --server-side -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.22/releases/cnpg-1.22.0.yaml
else
  echo "CRD already exists, skipping"
fi
echo "✅ cnpg operator"

echo "🕝 waiting for CNPG operator to be ready"
sleep 30
echo "✅ cnpg operator ready"

echo "🕝 cnpg cluster"
kubectl apply -f cnpg-cluster.yaml
kubectl wait cluster/timescaledb-operator -n iot --for=condition=Ready --timeout=300s
echo "✅ cnpg cluster"

echo "🕝 grpc server"
kubectl apply -f grpc-server.yaml
echo "✅ grpc server"

echo "🕝 grafana"
kubectl apply -f grafana.yaml
echo "✅ grafana"