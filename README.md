# MiTienda · dashboard HTML y Python

21 gráficos Seaborn recalculados en Python con filtros. `render.yaml` configura el servicio FastAPI y genera `index.html` durante el build. Las figuras solo se solicitan y cargan cuando responde el servidor; el HTML abierto como archivo no las incluye. El código se puede descargar como `.txt` desde el dashboard. El corte de 1.600 facturas se comparó con los seis CSV de `Mi_tienda.xlsx` y no hubo diferencias; los CSV originales y los contactos de clientes no se publican en este repositorio.

## Despliegue en Render

Conecta este repositorio a Render mediante **New → Blueprint** y confirma el plan Free. Render instalará dependencias, generará el HTML y publicará una URL `*.onrender.com`. Al mover filtros, la sección Seaborn mostrará «Seaborn recalculado con filtros».

## Prueba local

```bash
pip install -r requirements.txt
python build_dashboard.py
uvicorn app:app --host 127.0.0.1 --port 8050
```

Abre `http://127.0.0.1:8050/`. `/health` confirma las 1.600 filas. Para regenerar desde los seis CSV originales, usa `mitienda_dashboard.py --fuente csv --carpeta datos --servidor` con la carpeta `datos` de la entrega original. La conexión SQL opcional requiere una base real y `MITIENDA_DATABASE_URL`; no se simula una conexión activa.

## PostgreSQL en Supabase (punto adicional)

La migración `sql/001_mitienda_dw.sql` prepara tres tablas analíticas en un esquema privado, sin exponerlas a la API pública. `sql/002_mitienda_reader.sql` crea un usuario limitado a consultar esas tablas. El generador admite `--fuente csv --carpeta datos --cargar-sql` para cargar las tablas desde los seis CSV originales. El servidor FastAPI usa `MITIENDA_DATABASE_URL` como variable de entorno; con ella configurada, consulta PostgreSQL para el HTML y cada solicitud Seaborn, y `/health` informa `database_connected: true`. Para Render se utiliza la cadena **Session pooler** de Supabase, con SSL; la contraseña se establece solo en el entorno de Render y no se publica en GitHub.
