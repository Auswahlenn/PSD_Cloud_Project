variable "project" {}

variable "region" {
    default = "us-central1"
}

variable "broker_server" {
    description = "MQTT broker address (e.g. tcp://1.2.3.4:1883)"
}

variable "mqtt_topic" {
    description = "MQTT input topic name"
}

variable "pubsub_topic" {
    description = "Full Pub/Sub output topic path (projects/PROJECT/topics/TOPIC)"
}

variable "mqtt_username" {
    default = "guest"
}

variable "mqtt_password" {
    default   = "guest"
    sensitive = true
}
