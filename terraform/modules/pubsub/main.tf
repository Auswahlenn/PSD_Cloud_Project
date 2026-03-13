resource "google_pubsub_topic" "topics" {
    name = "mqtt-broker-topic"

    labels = {
        environment = "dev"
        }
}

resource "google_service_account" "hivemq_pubsub_bridge" {
    account_id   = "hivemq-pubsub-bridge"
    display_name = "HiveMQ Pub/Sub Bridge"
}

resource "google_pubsub_topic_iam_member" "hivemq_publisher" {
    topic  = google_pubsub_topic.topics.name
    role   = "roles/pubsub.publisher"
    member = "serviceAccount:${google_service_account.hivemq_pubsub_bridge.email}"
}

resource "google_pubsub_subscription" "topics_subscription" {
    name  = "mqtt-broker-subscription"
    topic = google_pubsub_topic.topics.name

    ack_deadline_seconds = 60

    retain_acked_messages = true

    message_retention_duration = "259200s"

    expiration_policy {
        ttl = "2592000s"
    }

     labels = {
        environment = "dev"
    }
}
  
