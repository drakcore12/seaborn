-- Esquema privado del corte analítico MiTienda. No se expone a la Data API.
CREATE SCHEMA IF NOT EXISTS mitienda_dw;
REVOKE ALL ON SCHEMA mitienda_dw FROM PUBLIC, anon, authenticated;

CREATE TABLE IF NOT EXISTS mitienda_dw.dw_mitienda_inventario (
  id varchar(40) PRIMARY KEY, bloque integer NOT NULL,
  producto varchar(240) NOT NULL, familia varchar(70) NOT NULL,
  stock integer NOT NULL CHECK (stock >= 0),
  precio numeric(18,2) NOT NULL CHECK (precio >= 0),
  proveedor varchar(180)
);
CREATE TABLE IF NOT EXISTS mitienda_dw.dw_mitienda_personal (
  id varchar(40) PRIMARY KEY, bloque integer NOT NULL,
  nombre varchar(180) NOT NULL, puesto varchar(80)
);
CREATE TABLE IF NOT EXISTS mitienda_dw.dw_mitienda_ventas (
  id varchar(70) PRIMARY KEY, factura varchar(40) NOT NULL,
  bloque integer NOT NULL, fecha varchar(10) NOT NULL,
  "timestamp" varchar(32) NOT NULL, mes varchar(7) NOT NULL,
  anio integer NOT NULL, mes_num integer NOT NULL,
  dia_semana integer NOT NULL, hora integer NOT NULL,
  cliente varchar(30) NOT NULL, zona varchar(100),
  empleado varchar(180), puesto varchar(80),
  producto_id varchar(30) NOT NULL REFERENCES mitienda_dw.dw_mitienda_inventario(id),
  producto varchar(240), familia varchar(70), proveedor varchar(180),
  cantidad integer NOT NULL CHECK (cantidad > 0),
  unitario numeric(18,2) NOT NULL CHECK (unitario >= 0),
  venta numeric(18,2) NOT NULL CHECK (venta = cantidad * unitario)
);
CREATE INDEX IF NOT EXISTS ix_mitienda_fecha ON mitienda_dw.dw_mitienda_ventas(fecha);
CREATE INDEX IF NOT EXISTS ix_mitienda_familia ON mitienda_dw.dw_mitienda_ventas(familia);
CREATE INDEX IF NOT EXISTS ix_mitienda_bloque ON mitienda_dw.dw_mitienda_ventas(bloque);
CREATE INDEX IF NOT EXISTS ix_mitienda_producto ON mitienda_dw.dw_mitienda_ventas(producto_id);
ALTER TABLE mitienda_dw.dw_mitienda_inventario ENABLE ROW LEVEL SECURITY;
ALTER TABLE mitienda_dw.dw_mitienda_personal ENABLE ROW LEVEL SECURITY;
ALTER TABLE mitienda_dw.dw_mitienda_ventas ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON ALL TABLES IN SCHEMA mitienda_dw FROM PUBLIC, anon, authenticated;
