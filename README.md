# MiTienda · dashboard HTML y Python

18 gráficos Plotly y tres gráficos Seaborn recalculados en Python con filtros. `render.yaml` configura el servicio FastAPI y genera `index.html` durante el build. El código se puede descargar como `.txt` desde el dashboard. El corte de 1.600 facturas se comparó con los seis CSV de `Mi_tienda.xlsx` y no hubo diferencias; los CSV originales y los contactos de clientes no se publican en este repositorio.

## Despliegue en Render

Conecta este repositorio a Render mediante **New → Blueprint** y confirma el plan Free. Render instalará dependencias, generará el HTML y publicará una URL `*.onrender.com`. Al mover filtros, la sección Seaborn mostrará «Seaborn recalculado con filtros».

## Prueba local

```bash
pip install -r requirements.txt
python build_dashboard.py
uvicorn app:app --host 127.0.0.1 --port 8050
```

Abre `http://127.0.0.1:8050/`. `/health` confirma las 1.600 filas. Para regenerar desde los seis CSV originales, usa `mitienda_dashboard.py --fuente csv --carpeta datos --servidor` con la carpeta `datos` de la entrega original. La conexión SQL opcional requiere una base real y `MITIENDA_DATABASE_URL`; no se simula una conexión activa.
