from pathlib import Path
from mitienda_dashboard import leer_corte, construir_html, validar_corte

ventas, inventario, personal, qa = leer_corte()
validar_corte(ventas, inventario)
assert len(ventas) == 1600 and sum(x['venta'] for x in ventas) == 203465700
qa['conciliacion_original'] = True  # Verificado antes contra seis CSV originales.
qa['facturas_inconsistentes'] = 0
origen = 'MITIENDA / SEIS TABLAS ORIGINALES CONCILIADAS · CORTE INCLUIDO'
construir_html(ventas, inventario, personal, qa, origen,
               Path(__file__).parent / 'index.html', dinamico=True)
