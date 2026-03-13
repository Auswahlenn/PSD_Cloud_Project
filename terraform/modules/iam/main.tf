resource "google_service_account" "vm_service_account" {
    account_id   = "vm-service-account"
    display_name = "VM Service Account"
}

resource "google_project_iam_member" "artifact_registry_reader" {
    project = var.project
    role    = "roles/artifactregistry.reader"
    member  = "serviceAccount:${google_service_account.vm_service_account.email}"
}

resource "google_project_iam_member" "dataflow_worker" {
    project = var.project
    role    = "roles/dataflow.worker"
    member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

resource "google_project_iam_member" "dataflow_pubsub_publisher" {
    project = var.project
    role    = "roles/pubsub.publisher"
    member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

data "google_project" "project" {
    project_id = var.project
}