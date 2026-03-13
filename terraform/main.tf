terraform{
    required_providers {
        google = {
            source  = "hashicorp/google"
            version = "7.23.0"
        }
    }
}

provider "google" {
  project = var.project
  region  = var.region
  zone    = var.zone
}

resource "google_compute_instance" "vm_instance" {
    name         = "vm-instance"
    machine_type = "e2-micro"
    zone         = var.zone

    boot_disk {
        initialize_params {
            image = "cos-cloud/cos-stable"
        }
    }

    network_interface {
        network = google_compute_network.vpc_network.self_link
        access_config {
                // Ephemeral public IP
        }
    }
}

resource "google_compute_firewall" "ssh" {
    name    = "allow-ssh"
    network = google_compute_network.vpc_network.self_link

    allow {
        protocol = "tcp"
        ports    = ["22"]
    }

    source_ranges = ["0.0.0.0/23"]
}


resource "google_compute_network" "vpc_network" {
    name = "vpc-network"
}

resource "google_artifact_registry_repository" "mqtt_broker" {
    location     = var.artifact_registry_location
    repository_id = var.artifact_registry_repository
    format       = "DOCKER"
}

resource "google_service_account" "vm_service_account" {
    provider    = google
    account_id   = "vm-service-account"
    display_name = "VM Service Account"
}

resource "google_project_iam_member" "vm_service_account_role" {
    project = var.project
    role    = "roles/artifactregistry.reader"
    member  = "serviceAccount:${google_service_account.vm_service_account.email}"
}

module "iam_binding" {
    source  = "./modules/iam"

    project = var.project

}