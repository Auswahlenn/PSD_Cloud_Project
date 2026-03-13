output "internal_ip" {
  value = google_compute_instance.vm_instance.network_interface[0].network_ip
}

output "external_ip" {
  value = google_compute_instance.vm_instance.network_interface[0].access_config[0].nat_ip
}

output "repository_url" {
  value = "${google_artifact_registry_repository.mqtt_broker.location}-docker.pkg.dev/${var.project}/${google_artifact_registry_repository.mqtt_broker.repository_id}"
}

output "pubsub_topic" {
  value = module.pubsub.topic_name
}

output "hivemq_bridge_service_account_email" {
  value = module.pubsub.bridge_service_account_email
}