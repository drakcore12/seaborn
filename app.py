"""Python Seaborn API for the public MiTienda dashboard."""
from collections import Counter, defaultdict
from io import BytesIO
from pathlib import Path
import base64
import json
import threading
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from mitienda_dashboard import construir_html
from warehouse import comprobar, leer_dashboard, ventas_filtradas

with (Path(__file__).parent / 'sales.json').open(encoding='utf-8') as source:
    VENTAS = json.load(source)
assert len(VENTAS) == 1600 and sum(r['venta'] for r in VENTAS) == 203465700
LOCK = threading.Lock()
HTML_LOCK = threading.Lock()
DB_URL = os.environ.get("MITIENDA_DATABASE_URL", "")
DB_HTML = Path("/tmp/mitienda_postgresql_dashboard.html")
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(CORSMiddleware,
    allow_origins=['https://mitienda-analitica-miguel.drackore.chatgpt.site'],
    allow_methods=['POST', 'GET'], allow_headers=['Content-Type'])

@app.get('/health')
def health():
    if DB_URL:
        try:
            stats = comprobar(DB_URL)
            if stats['rows'] != 1600 or stats['revenue_cop'] != 203465700:
                raise ValueError('Integridad de MiTienda no verificada')
        except Exception:
            raise HTTPException(status_code=503, detail='Base de datos no disponible')
        return {'ready': True, 'source': 'Supabase PostgreSQL / mitienda_dw',
                'database_connected': True, **stats}
    return {'ready': True, 'source': 'Corte MiTienda incluido',
            'database_connected': False, 'rows': len(VENTAS)}

@app.post('/api/seaborn')
async def seaborn_charts(request: Request):
    if int(request.headers.get('content-length', '0')) > 4096:
        raise HTTPException(status_code=413, detail='Filtro demasiado grande')
    try:
        body = await request.json()
        f = body['filters']
        if not isinstance(f, dict) or set(f) - {'start','end','block','family','zone','role','q'}:
            raise ValueError('Filtros no válidos')
        for key, value in f.items():
            if not isinstance(value, (int,str)) or len(str(value)) > 100:
                raise ValueError('Filtro no válido')
        block = int(f.get('block') or 0)
        if block not in (0,1,2):
            raise ValueError('Bloque no válido')
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        raise HTTPException(status_code=400, detail='Solicitud de filtros no válida')
    if DB_URL:
        try:
            selected = ventas_filtradas(DB_URL, f)
        except Exception:
            raise HTTPException(status_code=503, detail='No se pudo consultar PostgreSQL')
    else:
        selected = [r for r in VENTAS
        if (not f.get('start') or r['fecha'] >= f['start'])
        and (not f.get('end') or r['fecha'] <= f['end'])
        and (not block or r['bloque'] == block)
        and (not f.get('family') or r['familia'] == f['family'])
        and (not f.get('zone') or r['zona'] == f['zone'])
        and (not f.get('role') or r['puesto'] == f['role'])
        and (not f.get('q') or str(f['q']).lower() in r['producto'].lower()
             or str(f['q']).lower() in r['producto_id'].lower())]
    with LOCK:
        return {kind: imagen_seaborn(selected, kind) for kind in ('familias','calor','dispersion')}

def imagen_seaborn(ventas,tipo):
    """Genera un SVG con Seaborn para los registros filtrados."""
    sns.set_theme(style='darkgrid',font_scale=.9)
    bg='#ffffff';fg='#23354b';grid='#d8e1e9'
    plt.rcParams.update({'figure.facecolor':bg,'savefig.facecolor':bg,'axes.facecolor':bg,
                         'axes.labelcolor':fg,'text.color':fg,'xtick.color':'#53677c',
                         'ytick.color':'#53677c','axes.edgecolor':grid,'grid.color':grid,
                         'font.family':'DejaVu Sans','svg.fonttype':'none'})
    fig,ax=plt.subplots(figsize=(9,3.8),dpi=110)
    if not ventas:
        ax.text(.5,.5,'Sin registros para los filtros seleccionados',ha='center',va='center',transform=ax.transAxes,color=fg)
        ax.set_xticks([]);ax.set_yticks([])
    elif tipo=='familias':
        ag=defaultdict(float)
        for x in ventas: ag[x['familia']]+=x['venta']
        best=sorted(ag,key=ag.get,reverse=True)[:9]
        sns.barplot(x=[ag[x]/1e6 for x in best][::-1],y=best[::-1],ax=ax,color='#244f79')
        ax.set_xlabel('Millones de pesos colombianos');ax.set_ylabel('')
        ax.set_title('Ingresos por familia · Seaborn',pad=13,color=fg)
    elif tipo=='calor':
        arr=np.zeros((7,24),dtype=int)
        for x in ventas:arr[int(x['dia_semana']),int(x['hora'])]+=1
        hours=list(range(24))
        sns.heatmap(arr,ax=ax,cmap='mako',linewidths=.6,linecolor='#edf2f6',
                    xticklabels=[f'{h:02d}' for h in hours],
                    yticklabels=['Lun','Mar','Mié','Jue','Vie','Sáb','Dom'],
                    cbar_kws={'label':'Líneas de venta'})
        ax.set_xlabel('Hora');ax.set_ylabel('');ax.set_title('Actividad por día y hora · Seaborn',pad=13,color=fg)
    elif tipo=='dispersion':
        cnt=Counter(x['familia'] for x in ventas)
        fam=[x for x,_ in cnt.most_common(6)]
        sub=[x for x in ventas if x['familia'] in fam]
        if sub:
            sns.boxplot(x=[x['familia'] for x in sub],y=[x['venta']/1000 for x in sub],
                        order=fam,ax=ax,color='#6785ae',showfliers=True)
            ax.tick_params(axis='x',rotation=27)
        ax.set_xlabel('Familia');ax.set_ylabel('Importe de la línea (miles COP)')
        ax.set_title('Distribución del valor por familia · Seaborn',pad=13,color=fg)
    else:
        raise ValueError('tipo Seaborn desconocido')
    sns.despine(ax=ax)
    fig.tight_layout(pad=1.3)
    buf=BytesIO();fig.savefig(buf,format='svg',bbox_inches='tight');plt.close(fig)
    return 'data:image/svg+xml;base64,'+base64.b64encode(buf.getvalue()).decode('ascii')



@app.get('/')
def dashboard():
    if DB_URL:
        with HTML_LOCK:
            if not DB_HTML.exists():
                try:
                    ventas, inventario, personal, qa = leer_dashboard(DB_URL)
                    construir_html(ventas, inventario, personal, qa,
                        'POSTGRESQL / SUPABASE · MITIENDA', DB_HTML, dinamico=True)
                except Exception:
                    raise HTTPException(status_code=503, detail='No se pudo generar el dashboard desde PostgreSQL')
        return FileResponse(DB_HTML, media_type='text/html')
    return FileResponse(Path(__file__).parent / 'index.html', media_type='text/html')

@app.get('/Codigo_MiTienda.txt')
def codigo_txt():
    return FileResponse(Path(__file__).parent / 'mitienda_dashboard.py', media_type='text/plain; charset=utf-8')

@app.get('/mitienda_dashboard.py')
def codigo_py():
    return FileResponse(Path(__file__).parent / 'mitienda_dashboard.py', media_type='text/plain; charset=utf-8')
