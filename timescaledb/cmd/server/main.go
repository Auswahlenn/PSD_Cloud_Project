package main

import (
	"context"
	"log"
	"net"
	"os"
	"os/signal"
	"syscall"

	"cloud.google.com/go/pubsub"
	"github.com/pangjiade/GCP-ESP/timescaledb/internal/db"
	grpcserver "github.com/pangjiade/GCP-ESP/timescaledb/internal/grpc"
	"github.com/pangjiade/GCP-ESP/timescaledb/internal/subscriber"
	pb "github.com/pangjiade/GCP-ESP/timescaledb/pb"
	"google.golang.org/grpc"
	"google.golang.org/grpc/reflection"
)

func main() {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Config from environment
	dbURL := envOrDefault("DATABASE_URL", "postgres://postgres:postgres@localhost:5432/temperatures?sslmode=disable")
	grpcPort := envOrDefault("GRPC_PORT", "50051")
	projectID := envOrDefault("GCP_PROJECT", "project-4a8f3b06-8ff8-4efd-a4d")
	subscriptionID := envOrDefault("PUBSUB_SUBSCRIPTION", "mqtt-broker-subscription")

	// Connect to TimescaleDB
	database, err := db.New(ctx, dbURL)
	if err != nil {
		log.Fatalf("failed to connect to database: %v", err)
	}
	defer database.Close()
	log.Println("connected to TimescaleDB")

	// Start Pub/Sub subscriber
	pubsubClient, err := pubsub.NewClient(ctx, projectID)
	if err != nil {
		log.Fatalf("failed to create pubsub client: %v", err)
	}
	defer pubsubClient.Close()

	sub := subscriber.New(database, pubsubClient, subscriptionID)
	go func() {
		if err := sub.Start(ctx); err != nil {
			log.Printf("subscriber error: %v", err)
		}
	}()
	log.Println("Pub/Sub subscriber started")

	// Start gRPC server
	lis, err := net.Listen("tcp", ":"+grpcPort)
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}

	srv := grpc.NewServer()
	pb.RegisterTemperatureServiceServer(srv, grpcserver.NewServer(database))
	reflection.Register(srv)

	go func() {
		log.Printf("gRPC server listening on :%s", grpcPort)
		if err := srv.Serve(lis); err != nil {
			log.Fatalf("failed to serve: %v", err)
		}
	}()

	// Graceful shutdown
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	<-sigCh
	log.Println("shutting down...")
	srv.GracefulStop()
	cancel()
}

func envOrDefault(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
