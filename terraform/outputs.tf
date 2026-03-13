output "internal_ip" {
  value = module.mqtt_broker.internal_ip
}

output "external_ip" {
  value = module.mqtt_broker.external_ip
}

output "mqtt_broker_endpoint" {
  value = "${module.mqtt_broker.external_ip}:1883"
}

output "repository_url" {
  value = "${google_artifact_registry_repository.mqtt_broker.location}-docker.pkg.dev/${var.project}/${google_artifact_registry_repository.mqtt_broker.repository_id}"
}

output "pubsub_topic" {
  value = module.pubsub.topic_name
}

output "pubsub_subscription" {
  value = module.pubsub.subscription_name
}