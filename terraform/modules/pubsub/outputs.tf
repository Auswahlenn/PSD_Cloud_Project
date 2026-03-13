output "topic_name" {
	value = google_pubsub_topic.topics.name
}

output "subscription_name" {
	value = google_pubsub_subscription.topics_subscription.name
}

output "bridge_service_account_email" {
	value = google_service_account.hivemq_pubsub_bridge.email
}
