resource "google_compute_address" "mqtt_broker_ip" {
  name   = "mqtt-broker-ip"
  region = var.region
}

resource "google_compute_network" "mqtt_network" {
  name                    = var.network_name
  auto_create_subnetworks = true
}

resource "google_compute_firewall" "allow_ssh" {
  name    = "${var.network_name}-allow-ssh"
  network = google_compute_network.mqtt_network.self_link

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = var.allowed_ssh_cidrs
  target_tags   = ["mqtt-broker"]
}

resource "google_compute_firewall" "allow_mqtt" {
  name    = "${var.network_name}-allow-mqtt"
  network = google_compute_network.mqtt_network.self_link

  allow {
    protocol = "tcp"
    ports    = ["1883"]
  }

  source_ranges = var.allowed_mqtt_cidrs
  target_tags   = ["mqtt-broker"]
}

resource "google_compute_instance" "mqtt_broker" {
  name         = var.instance_name
  machine_type = var.machine_type
  zone         = var.zone
  tags         = ["mqtt-broker"]

  service_account {
    email  = var.service_account_email
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
    }
  }

  network_interface {
    network = google_compute_network.mqtt_network.self_link

    access_config {
      nat_ip = google_compute_address.mqtt_broker_ip.address
    }
  }

  metadata_startup_script = <<-EOT
    #!/bin/bash
    set -euo pipefail
    exec > >(tee -a /var/log/mqtt-startup.log) 2>&1

    apt-get update
    apt-get install -y docker.io curl jq
    systemctl enable docker
    systemctl start docker

    IMAGE="${var.container_image}"
    REGISTRY_HOST="$(echo "$IMAGE" | cut -d/ -f1)"
    ACCESS_TOKEN="$(curl -s -H 'Metadata-Flavor: Google' 'http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token' | jq -r '.access_token')"

    if [ -z "$ACCESS_TOKEN" ]; then
      echo "Failed to get access token from metadata server"
      exit 1
    fi

    echo "$ACCESS_TOKEN" | docker login -u oauth2accesstoken --password-stdin "https://$REGISTRY_HOST"
    docker pull "$IMAGE"

    mkdir -p /opt/mosquitto/config
    cat > /opt/mosquitto/config/mosquitto.conf <<'EOF'
allow_anonymous true
listener 1883
persistence true
persistence_location /mosquitto/data/
log_dest stdout
EOF

    docker rm -f mqtt-broker || true
    docker run -d \
      --name mqtt-broker \
      --restart unless-stopped \
      -p 1883:1883 \
      -v /opt/mosquitto/config:/mosquitto/config \
      "$IMAGE"
  EOT
}
