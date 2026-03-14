resource "google_dataflow_flex_template_job" "mqtt_to_pubsub" {
    provider                = google-beta
    name                    = "mqtt-to-pubsub"
    project                 = var.project
    region                  = var.region
    on_delete               = "cancel"
    skip_wait_on_job_termination = true

    container_spec_gcs_path = "gs://dataflow-templates-${var.region}/latest/flex/Mqtt_to_PubSub"

    parameters = {
        brokerServer      = var.broker_server
        inputTopic        = var.mqtt_topic
        outputTopic       = var.pubsub_topic
        username          = var.mqtt_username
        password          = var.mqtt_password
        workerMachineType = var.worker_machine_type
        numWorkers        = tostring(var.num_workers)
        maxNumWorkers     = tostring(var.max_num_workers)
    }

    additional_experiments = ["enable_streaming_engine"]
}
