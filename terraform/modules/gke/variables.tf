variable "project" {}

variable "region" {
    default = "us-central1"
}

variable "zone" {
    default = "us-central1-a"
}

variable "cluster_name" {
    default = "iot-cluster"
}

variable "node_count" {
    default = 2
}

variable "machine_type" {
    default = "e2-medium"
}

variable "disk_size_gb" {
    default = 30
}

variable "service_account_email" {
    description = "Service account for GKE nodes"
}
