package subscriber

import (
	"context"
	"encoding/json"
	"log"
	"time"

	"cloud.google.com/go/pubsub"
	"github.com/pangjiade/GCP-ESP/timescaledb/internal/db"
)

type message struct {
	Device string  `json:"device"`
	Metric string  `json:"metric"`
	Value  float64 `json:"value"`
	Unit   string  `json:"unit"`
	Ts     string  `json:"ts"`
}

type Subscriber struct {
	db     *db.DB
	client *pubsub.Client
	subID  string
}

func New(database *db.DB, client *pubsub.Client, subscriptionID string) *Subscriber {
	return &Subscriber{
		db:     database,
		client: client,
		subID:  subscriptionID,
	}
}

func (s *Subscriber) Start(ctx context.Context) error {
	sub := s.client.Subscription(s.subID)
	log.Printf("listening on Pub/Sub subscription: %s", s.subID)

	return sub.Receive(ctx, func(_ context.Context, msg *pubsub.Message) {
		var m message
		if err := json.Unmarshal(msg.Data, &m); err != nil {
			log.Printf("failed to unmarshal message: %v", err)
			msg.Nack()
			return
		}

		ts, err := time.Parse(time.RFC3339Nano, m.Ts)
		if err != nil {
			ts = time.Now()
		}

		reading := db.TemperatureReading{
			Time:   ts,
			Device: m.Device,
			Value:  m.Value,
			Unit:   m.Unit,
		}

		if err := s.db.InsertTemperature(context.Background(), reading); err != nil {
			log.Printf("failed to insert: %v", err)
			msg.Nack()
			return
		}

		log.Printf("stored: device=%s value=%.2f%s", m.Device, m.Value, m.Unit)
		msg.Ack()
	})
}
