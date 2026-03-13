package db

import (
	"context"
	"fmt"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

type TemperatureReading struct {
	Time   time.Time
	Device string
	Value  float64
	Unit   string
}

type DB struct {
	pool *pgxpool.Pool
}

func New(ctx context.Context, connString string) (*DB, error) {
	pool, err := pgxpool.New(ctx, connString)
	if err != nil {
		return nil, fmt.Errorf("connect to db: %w", err)
	}
	if err := pool.Ping(ctx); err != nil {
		return nil, fmt.Errorf("ping db: %w", err)
	}
	return &DB{pool: pool}, nil
}

func (d *DB) Close() {
	d.pool.Close()
}

func (d *DB) InsertTemperature(ctx context.Context, r TemperatureReading) error {
	_, err := d.pool.Exec(ctx,
		"INSERT INTO temperatures (time, device, value, unit) VALUES ($1, $2, $3, $4)",
		r.Time, r.Device, r.Value, r.Unit,
	)
	return err
}

func (d *DB) GetTemperatures(ctx context.Context, device string, start, end time.Time, limit int32) ([]TemperatureReading, error) {
	query := "SELECT time, device, value, unit FROM temperatures WHERE device = $1 AND time >= $2 AND time <= $3 ORDER BY time DESC LIMIT $4"
	rows, err := d.pool.Query(ctx, query, device, start, end, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var readings []TemperatureReading
	for rows.Next() {
		var r TemperatureReading
		if err := rows.Scan(&r.Time, &r.Device, &r.Value, &r.Unit); err != nil {
			return nil, err
		}
		readings = append(readings, r)
	}
	return readings, rows.Err()
}

func (d *DB) GetLatest(ctx context.Context, device string) (*TemperatureReading, error) {
	var r TemperatureReading
	err := d.pool.QueryRow(ctx,
		"SELECT time, device, value, unit FROM temperatures WHERE device = $1 ORDER BY time DESC LIMIT 1",
		device,
	).Scan(&r.Time, &r.Device, &r.Value, &r.Unit)
	if err != nil {
		return nil, err
	}
	return &r, nil
}
