resource "google_container_cluster" "primary" {
    name     = var.cluster_name
    location = var.zone
    project  = var.project

    initial_node_count       = 1
    remove_default_node_pool = true

    deletion_protection = false
}

resource "google_container_node_pool" "primary_nodes" {
    name     = "${var.cluster_name}-node-pool"
    location = var.zone
    project  = var.project
    cluster  = google_container_cluster.primary.name

    node_count = var.node_count

    node_config {
        machine_type    = var.machine_type
        disk_size_gb    = var.disk_size_gb
        service_account = var.service_account_email

        oauth_scopes = [
            "https://www.googleapis.com/auth/cloud-platform",
        ]
    }
}
