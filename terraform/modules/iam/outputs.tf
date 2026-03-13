output "iam" {
    value = {
        service_account_email = google_service_account.vm_service_account.email
    }
}