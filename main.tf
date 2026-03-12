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