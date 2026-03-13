output "job_id" {
    value = google_dataflow_flex_template_job.mqtt_to_pubsub.job_id
}

output "job_name" {
    value = google_dataflow_flex_template_job.mqtt_to_pubsub.name
}
