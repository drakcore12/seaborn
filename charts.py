"""Visualizaciones MiTienda producidas en el servidor con Seaborn."""
from collections import Counter, defaultdict
from io import BytesIO
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

KINDS = ('ch_months','ch_years','ch_month_orders','ch_ticket','ch_week','ch_hour',
         'ch_family','ch_donut','ch_product','ch_qty','ch_zone','ch_customers',
         'ch_employees','ch_roles','ch_providers','ch_stocks','ch_refs','ch_stockrange',
         'familias','calor','dispersion')
DAYS = ['Lun','Mar','Mié','Jue','Vie','Sáb','Dom']

def _sum(rows, key, value='venta'):
    out=defaultdict(float)
    for r in rows: out[str(r.get(key) or 'Sin dato')]+=float(r[value])
    return out

def _bar(ax, data, horizontal=False, limit=10, percent=False):
    items=sorted(data.items(),key=lambda item:item[1],reverse=True)[:limit]
    if not items: return
    labels=[x[0][:34] for x in items]
    values=[x[1] for x in items]
    if percent:
        total=sum(data.values()) or 1
        values=[100*x/total for x in values]
    if horizontal:
        sns.barplot(x=values[::-1],y=labels[::-1],ax=ax,color='#4776a8',errorbar=None)
    else:
        sns.barplot(x=labels,y=values,ax=ax,color='#4776a8',errorbar=None)
        ax.tick_params(axis='x',rotation=28)
    ax.set(xlabel='Participación (%)' if percent else '',ylabel='')

def render(kind, sales, inventory, currency='COP', trm=4000):
    if kind not in KINDS: raise ValueError('Visualización no válida')
    sns.set_theme(style='whitegrid',font='DejaVu Sans',font_scale=.86,
                  rc={'axes.facecolor':'#ffffff','figure.facecolor':'#ffffff',
                      'grid.color':'#edf0f4','axes.edgecolor':'#dbe2ea',
                      'axes.labelcolor':'#53657a','text.color':'#24364a',
                      'svg.fonttype':'none'})
    fig,ax=plt.subplots(figsize=(8.8,4.0),dpi=95)
    scale=trm if currency=='USD' else 1
    rows=sales
    if kind in ('ch_stocks','ch_refs','ch_stockrange'): rows=inventory
    if not rows:
        ax.text(.5,.5,'Sin registros para los filtros seleccionados',ha='center',va='center',transform=ax.transAxes,color='#64748b')
        ax.set_xticks([]);ax.set_yticks([])
    elif kind in ('ch_months','ch_years','ch_week','ch_hour','ch_month_orders','ch_ticket'):
        if kind=='ch_months':
            d=_sum(sales,'mes');labels=sorted(d);values=[d[x]/scale for x in labels]
            sns.lineplot(x=labels,y=values,marker='o',color='#3478c0',linewidth=2.5,ax=ax)
        elif kind=='ch_years':
            _bar(ax,{k:v/scale for k,v in _sum(sales,'anio').items()})
        elif kind=='ch_month_orders':
            d=defaultdict(set)
            for r in sales:d[r['mes']].add(r['factura'])
            labels=sorted(d);sns.barplot(x=labels,y=[len(d[x]) for x in labels],color='#4776a8',ax=ax)
        elif kind=='ch_ticket':
            d=defaultdict(lambda:defaultdict(float))
            for r in sales:d[r['mes']][r['factura']]+=float(r['venta'])
            labels=sorted(d);sns.lineplot(x=labels,y=[sum(d[x].values())/len(d[x])/scale for x in labels],marker='o',color='#b48a51',ax=ax)
        elif kind=='ch_week':
            d=defaultdict(float)
            for r in sales:d[int(r['dia_semana'])]+=float(r['venta'])/scale
            sns.barplot(x=DAYS,y=[d[x] for x in range(7)],color='#4776a8',ax=ax)
        else:
            d=Counter(int(r['hora']) for r in sales)
            sns.barplot(x=list(range(24)),y=[d[x] for x in range(24)],color='#4776a8',ax=ax)
            ax.tick_params(axis='x',rotation=60)
        if kind in ('ch_months','ch_ticket','ch_month_orders'):ax.tick_params(axis='x',rotation=45)
        ax.set(xlabel='',ylabel=('Importe (USD)' if currency=='USD' else 'Importe (COP)') if kind in ('ch_months','ch_years','ch_ticket','ch_week') else 'Facturas / líneas')
    elif kind in ('ch_customers','ch_stockrange'):
        if kind=='ch_customers':
            d=defaultdict(set)
            for r in sales:d[r['cliente']].add(r['factura'])
            n=Counter(min(len(x),5) for x in d.values())
            labels=['1','2','3','4','5+'];values=[n[x] for x in (1,2,3,4,5)]
        else:
            labels=['0','1–10','11–20','21–50','>50'];n=Counter(0 if r['stock']==0 else 1 if r['stock']<=10 else 2 if r['stock']<=20 else 3 if r['stock']<=50 else 4 for r in inventory)
            values=[n[x] for x in range(5)]
        sns.barplot(x=labels,y=values,color='#4776a8',ax=ax);ax.set(xlabel='Facturas por cliente' if kind=='ch_customers' else 'Unidades en stock',ylabel='Clientes' if kind=='ch_customers' else 'Referencias')
    elif kind=='calor':
        import numpy as np
        matrix=np.zeros((7,24),dtype=int)
        for r in sales:matrix[int(r['dia_semana']),int(r['hora'])]+=1
        sns.heatmap(matrix,cmap='Blues',ax=ax,yticklabels=DAYS,xticklabels=[str(x) for x in range(24)])
        ax.set(xlabel='Hora',ylabel='Día')
    elif kind=='dispersion':
        families=Counter(r['familia'] for r in sales)
        top=[x for x,_ in families.most_common(6)]
        subset=[r for r in sales if r['familia'] in top]
        sns.boxplot(x=[r['familia'] for r in subset],y=[float(r['venta'])/scale for r in subset],order=top,color='#76a0c9',ax=ax)
        ax.tick_params(axis='x',rotation=30);ax.set(xlabel='',ylabel='Valor de línea ('+currency+')')
    else:
        field={'ch_family':'familia','ch_donut':'familia','ch_product':'producto','ch_qty':'familia',
               'ch_zone':'zona','ch_employees':'empleado','ch_roles':'puesto','ch_providers':'proveedor',
               'ch_stocks':'familia','ch_refs':'familia','familias':'familia'}[kind]
        if kind=='ch_refs':d=Counter(str(r[field]) for r in inventory)
        elif kind=='ch_stocks':d=_sum(inventory,field,'stock')
        else:d=_sum(sales,field,'cantidad' if kind=='ch_qty' else 'venta')
        if kind not in ('ch_qty','ch_stocks','ch_refs'):
            d={k:v/scale for k,v in d.items()}
        _bar(ax,d,horizontal=True,limit=8 if kind=='ch_product' else 10,percent=kind=='ch_donut')
        if kind!='ch_donut':ax.set_xlabel(('Unidades' if kind in ('ch_qty','ch_stocks','ch_refs') else 'Importe ('+currency+')'))
    sns.despine(ax=ax)
    fig.tight_layout(pad=1.1)
    stream=BytesIO();fig.savefig(stream,format='svg',bbox_inches='tight');plt.close(fig)
    return 'data:image/svg+xml;base64,'+base64.b64encode(stream.getvalue()).decode('ascii')
