-- Inicialización de la base de datos P2P

-- Habilitar extensión TimescaleDB
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Habilitar extensión para UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Crear esquema para series temporales
CREATE SCHEMA IF NOT EXISTS timeseries;

-- Comentarios
COMMENT ON SCHEMA timeseries IS 'Esquema para datos de series temporales de precios y operaciones';

-- Dar permisos
GRANT ALL ON SCHEMA public TO p2p_user;
GRANT ALL ON SCHEMA timeseries TO p2p_user;

-- Configuración inicial
SELECT 'Database initialized successfully' AS status;
