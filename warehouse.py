"""Lecturas SQL de MiTienda en el esquema privado PostgreSQL de Supabase."""
from sqlalchemy import text
from mitienda_dashboard import motor_sql, leer_sql


def comprobar(url):
    engine = motor_sql(url)
    try:
        with engine.connect() as con:
            row = con.execute(text('''SELECT
                     (SELECT count(*) FROM mitienda_dw.dw_mitienda_ventas) AS lineas,
                     (SELECT coalesce(sum(venta),0) FROM mitienda_dw.dw_mitienda_ventas) AS ingresos,
                     (SELECT count(*) FROM mitienda_dw.dw_mitienda_inventario) AS productos,
                     (SELECT count(*) FROM mitienda_dw.dw_mitienda_personal) AS empleados,
                     (SELECT count(*) FROM mitienda_dw.dw_mitienda_ventas v
                        LEFT JOIN mitienda_dw.dw_mitienda_inventario i ON i.id=v.producto_id
                        WHERE i.id IS NULL) AS sin_producto,
                     to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"') AS checked_at''')).mappings().one()
            return {'rows': int(row['lineas']), 'revenue_cop': int(row['ingresos']),
                    'products': int(row['productos']), 'employees': int(row['empleados']),
                    'orphan_sales': int(row['sin_producto']), 'checked_at': row['checked_at']}
    finally:
        engine.dispose()


def leer_dashboard(url):
    return leer_sql(url)


def ventas_filtradas(url, filtros):
    condiciones = []
    parametros = {}
    for clave, columna in [('start', 'fecha'), ('end', 'fecha'),
                            ('block', 'bloque'), ('family', 'familia'),
                            ('zone', 'zona'), ('role', 'puesto')]:
        valor = filtros.get(clave)
        if valor:
            op = '>=' if clave == 'start' else '<=' if clave == 'end' else '='
            nombre = 'p_' + clave
            condiciones.append(f'{columna} {op} :{nombre}')
            parametros[nombre] = valor
    if filtros.get('q'):
        condiciones.append('''(position(lower(:p_q) in lower(producto)) > 0
                          OR position(lower(:p_q) in lower(producto_id)) > 0)''')
        parametros['p_q'] = filtros['q']
    query = 'SELECT familia, venta, dia_semana, hora FROM mitienda_dw.dw_mitienda_ventas'
    if condiciones:
        query += ' WHERE ' + ' AND '.join(condiciones)
    engine = motor_sql(url)
    try:
        with engine.connect() as con:
            return [{**row, 'venta': float(row['venta'])}
                    for row in con.execute(text(query), parametros).mappings()]
    finally:
        engine.dispose()
