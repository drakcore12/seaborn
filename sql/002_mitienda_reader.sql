-- Usuario exclusivo de consulta para el servidor Python.
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mitienda_reader') THEN
    CREATE ROLE mitienda_reader LOGIN;
  END IF;
END $$;

GRANT USAGE ON SCHEMA mitienda_dw TO mitienda_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA mitienda_dw TO mitienda_reader;

CREATE POLICY mitienda_reader_select ON mitienda_dw.dw_mitienda_inventario
  FOR SELECT TO mitienda_reader USING (true);
CREATE POLICY mitienda_reader_select ON mitienda_dw.dw_mitienda_personal
  FOR SELECT TO mitienda_reader USING (true);
CREATE POLICY mitienda_reader_select ON mitienda_dw.dw_mitienda_ventas
  FOR SELECT TO mitienda_reader USING (true);

-- La contraseña se asigna fuera del repositorio y se almacena en Render.
