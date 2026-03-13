resource "google_project_iam_binding" "artifact_registry_reader" {
    project = var.project
    role    = "roles/artifactregistry.reader"
    members = [
        "serviceAccount:${google_service_account.vm_service_account.email}"
    ]
}