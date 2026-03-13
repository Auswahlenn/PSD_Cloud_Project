output "topic_name" {
	value = google_pubsub_topic.topics.name
}

output "subscription_name" {
	value = google_pubsub_subscription.topics_subscription.name
}
