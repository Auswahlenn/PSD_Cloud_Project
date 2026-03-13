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

locals {
    default_mqtt_container_image = "${google_artifact_registry_repository.mqtt_broker.location}-docker.pkg.dev/${var.project}/${google_artifact_registry_repository.mqtt_broker.repository_id}/mqtt_broker:latest"
    mqtt_container_image         = var.mqtt_container_image != "" ? var.mqtt_container_image : local.default_mqtt_container_image
}

# -----------------------------------------------------------------------------
# Docker Image also known as Artifact Registry Repository
# -----------------------------------------------------------------------------
resource "google_artifact_registry_repository" "mqtt_broker" {
    location     = var.artifact_registry_location
    repository_id = var.artifact_registry_repository
    format       = "DOCKER"
}


# -----------------------------------------------------------------------------
# Modules
# -----------------------------------------------------------------------------
module "iam_binding" {
    source  = "./modules/iam"

    project = var.project

}

module "mqtt_broker" {
    source = "./modules/mqtt_broker"

    region             = var.region
    zone               = var.zone
    allowed_mqtt_cidrs = var.allowed_mqtt_cidrs
    allowed_ssh_cidrs  = var.allowed_ssh_cidrs
    container_image    = local.mqtt_container_image
    service_account_email = module.iam_binding.service_account_email
}

module "pubsub" {
    source  = "./modules/pubsub"

    project                       = var.project
    publisher_service_account_email = module.iam_binding.service_account_email
}