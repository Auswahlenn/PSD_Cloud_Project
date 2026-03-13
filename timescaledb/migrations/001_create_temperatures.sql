CREATE TABLE IF NOT EXISTS temperatures (
    time        TIMESTAMPTZ NOT NULL,
    device      TEXT        NOT NULL,
    value       DOUBLE PRECISION NOT NULL,
    unit        TEXT        NOT NULL DEFAULT 'C'
);

SELECT create_hypertable('temperatures', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_temperatures_device_time ON temperatures (device, time DESC);
