package grpc

import (
	"context"
	"log"

	"github.com/pangjiade/GCP-ESP/timescaledb/internal/db"
	pb "github.com/pangjiade/GCP-ESP/timescaledb/pb"
	"google.golang.org/protobuf/types/known/timestamppb"
)

type Server struct {
	pb.UnimplementedTemperatureServiceServer
	db *db.DB
}

func NewServer(database *db.DB) *Server {
	return &Server{db: database}
}

func (s *Server) RecordTemperature(ctx context.Context, req *pb.TemperatureRequest) (*pb.TemperatureResponse, error) {
	reading := db.TemperatureReading{
		Time:   req.Timestamp.AsTime(),
		Device: req.Device,
		Value:  req.Value,
		Unit:   req.Unit,
	}
	if err := s.db.InsertTemperature(ctx, reading); err != nil {
		log.Printf("failed to insert temperature: %v", err)
		return &pb.TemperatureResponse{Success: false}, err
	}
	return &pb.TemperatureResponse{Success: true}, nil
}

func (s *Server) GetTemperatures(ctx context.Context, req *pb.GetTemperaturesRequest) (*pb.GetTemperaturesResponse, error) {
	limit := req.Limit
	if limit == 0 {
		limit = 100
	}
	readings, err := s.db.GetTemperatures(ctx, req.Device, req.Start.AsTime(), req.End.AsTime(), limit)
	if err != nil {
		return nil, err
	}

	var pbReadings []*pb.TemperatureReading
	for _, r := range readings {
		pbReadings = append(pbReadings, &pb.TemperatureReading{
			Device:    r.Device,
			Value:     r.Value,
			Unit:      r.Unit,
			Timestamp: timestamppb.New(r.Time),
		})
	}
	return &pb.GetTemperaturesResponse{Readings: pbReadings}, nil
}

func (s *Server) GetLatestTemperature(ctx context.Context, req *pb.GetLatestRequest) (*pb.TemperatureReading, error) {
	r, err := s.db.GetLatest(ctx, req.Device)
	if err != nil {
		return nil, err
	}
	return &pb.TemperatureReading{
		Device:    r.Device,
		Value:     r.Value,
		Unit:      r.Unit,
		Timestamp: timestamppb.New(r.Time),
	}, nil
}
