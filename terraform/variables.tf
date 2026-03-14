variable project { }

variable region {
    default = "us-central1"
}

variable zone {
    default = "us-central1-a"
}

variable artifact_registry_location {
    default = "us-central1"
}

variable artifact_registry_repository {
    default = "mqtt-broker"
}

variable pubsub_topic {
    default = "mqtt-broker-topic"
}

variable dataflow_region {
    description = "Region for Dataflow jobs (us-central1 has capacity issues on free tier)"
    default     = "us-west1"
}

variable mqtt_container_image {
    type    = string
    default = ""
}

variable allowed_mqtt_cidrs {
    type    = list(string)
    default = ["0.0.0.0/0"]
}

variable allowed_ssh_cidrs {
    type    = list(string)
    default = ["0.0.0.0/0"]
}