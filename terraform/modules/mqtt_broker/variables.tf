variable "region" {
  type = string
}

variable "zone" {
  type = string
}

variable "instance_name" {
  type    = string
  default = "mqtt-broker-vm"
}

variable "machine_type" {
  type    = string
  default = "e2-small"
}

variable "network_name" {
  type    = string
  default = "mqtt-network"
}

variable "allowed_mqtt_cidrs" {
  type    = list(string)
  default = ["0.0.0.0/0"]
}

variable "allowed_ssh_cidrs" {
  type    = list(string)
  default = ["0.0.0.0/0"]
}

variable "container_image" {
  type = string
}

variable "service_account_email" {
  type = string
}
