output "instance_name" {
  value = google_compute_instance.mqtt_broker.name
}

output "internal_ip" {
  value = google_compute_instance.mqtt_broker.network_interface[0].network_ip
}

output "external_ip" {
  value = google_compute_address.mqtt_broker_ip.address
}

output "network_name" {
  value = google_compute_network.mqtt_network.name
}
