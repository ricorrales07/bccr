import dash
from dash.dependencies import Input, Output, State
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import plotly.express as px
from bccr import SW
import io
from contextlib import redirect_stdout

from datetime import date

import numpy as np


ayuda = """
# Acerca del paquete bccr

## Una API de Python para descargar datos del Banco Central de Costa Rica

El propósito de esta interfase gráfica es facilitar la búsqueda y descarga de indicadores publicados por el [Banco Central de Costa Rica](https://www.bccr.fi.cr/) por medio de su servicio web. 

La interfase está basada en el paquete de Python `bccr` desarrollada por el autor de esta interfase. El paquete ofrece dos clases para buscar datos y descargarlos:

* [`ServicioWeb`](http://randall-romero.com/demo-bccr-servicioweb/): descarga indicadores individuales del [servicio web](https://www.bccr.fi.cr/seccion-indicadores-economicos/servicio-web) del Banco Central.
* [`PaginaWeb`](http://randall-romero.com/demo-bccr-paginaweb/): descarga cuadros individuales (algunos con un solo indicador, otros con varios), de la página de [indicadores económicos](https://www.bccr.fi.cr/seccion-indicadores-economicos/indicadores-económicos).

En esta versión, la interfase solo permite descargar datos a través del `Servicioweb`. 

Los datos se descargan y se presentan en una tabla, en la cual cada fila corresponde a un período (día, mes, trimestre, año) y cada columna a un indicador. 

### Acerca del autor
Randall Romero Aguilar, PhD

[randall.romero@outlook.com](mailto:randall.romero@outlook.com)

### Aviso

Este paquete no es un producto oficial de BCCR. El autor lo provee para facilitar el manejo de datos, pero no ofrece ninguna garantía acerca de su correcto funcionamiento. 
"""






app = dash.Dash(__name__)

app.layout = html.Div([
    html.Div(
        children=[
            html.H1('Indicadores a descargar'),
            dash_table.DataTable(
                id='seleccionar-indicadores',
                columns=[
                    {'name': 'Nombre', 'id': 'nombre', 'deletable': False, 'renamable': False},
                    {'name': 'Código', 'id': 'código', 'deletable': False, 'renamable': False},
                ],
                data=[{'nombre': 'Inflación', 'código': '25485'}],
                editable=True,
                row_deletable=True
            ), # fin tabla de códigos a descargar
            html.Button('Agregar otro código', id='agregar-codigo-button', n_clicks=0),
            html.H2('Rango de fechas a consultar'),
            dcc.DatePickerSingle(
                id='fecha-primera-observación',
                display_format='YYYY/MM/DD',
                min_date_allowed=date(1950, 1, 1),
                max_date_allowed=date(2030,12,31),
                initial_visible_month=date(1990, 1, 1),
                date=date(1990, 1, 1)
            ), # fin fecha de inicio
            dcc.DatePickerSingle(
                id='fecha-última-observación',
                display_format='YYYY/MM/DD',
                min_date_allowed=date(1950, 1, 1),
                max_date_allowed=date(2030,12,31),
                initial_visible_month=date(1990, 1, 1),
                date=date.today()
            ), # fin fecha de cierre
            html.H2('Frecuencia de los datos'),
            dcc.Dropdown(
                id='frecuencia',
                options=[
                    {'label': 'Original', 'value': 'O'},
                    {'label': 'Anual', 'value': 'A'},
                    {'label': 'Semestral', 'value': '6M'},
                    {'label': 'Trimestral', 'value': 'Q'},
                    {'label': 'Mensual', 'value': 'M'},
                    {'label': 'Semanal', 'value': 'W'},
                    {'label': 'Diaria', 'value': 'D'}
                ],
                value='O'
            ), # fin de Frecuencia de los datos
            html.H2('Función para cambiar frecuencia de datos'),
            dcc.Dropdown(
                id='func',
                options=[
                    {'label': 'Promedio', 'value': 'mean'},
                    {'label': 'Suma', 'value': 'sum'},
                    {'label': 'Último día', 'value': 'last'},
                    {'label': 'Primer día', 'value': 'first'},
                ],
                value='mean'
            ), # fin de función para cambiar frecuencia de los datos
            html.H2('Rellenar datos faltantes'),
            dcc.Dropdown(
                id='fillna',
                options=[
                    {'label': 'No', 'value': 'no'},
                    {'label': 'Usar último disponible', 'value': 'last'},
                    {'label': 'Usar próximo disponible', 'value': 'next'},
                ],
                value='no'
            ), # fin de función para cambiar frecuencia de los datos
            html.Button('Consultar datos', id='consultar-datos-button', n_clicks=0),
            html.Img(src='https://randall-romero.github.io/econometria/_static/r2-logo.png',width='80%'),
        ],
        style={'width': '20%', 'display': 'inline-block'}
    ), # fin panel controles
    html.Div( children=[
                 dcc.Tabs([
                     dcc.Tab(label='Datos',
                             children=[
                                 dash_table.DataTable(
                                     id='datos-descargados',
                                     editable=False,
                                     row_deletable=False
                                 )
                             ],
                             ), #final tab 'Datos'
                     dcc.Tab(label='Gráfico',
                             children=[
                                 dcc.Graph(id='gráfico-datos')
                             ],
                             ), #final tab 'Datos'
                     dcc.Tab(label='Buscar códigos',
                             children=[
                                 dcc.Input(
                                     id='buscar-códigos',
                                     placeholder='Escriba acá los términos que desea buscar...',
                                     value='',
                                     style={'padding': 10, 'width': '50%'}
                                 ),
                                 html.Button('Buscar', id='buscar-códigos-button', n_clicks=0),
                                 html.P('Tipo de búsqueda'),
                                 dcc.RadioItems(
                                     id='tipo-búsqueda',
                                     options=[
                                         {'label': 'frase exacta', 'value': 'frase'},
                                         {'label': 'todas las palabras', 'value': 'todos'},
                                         {'label': 'alguna de las palabras', 'value': 'algunos'}
                                     ],
                                     value='frase',
                                     labelStyle={'display': 'inline-block'}
                                 ),
                                 dcc.Textarea(id='buscar-mensaje',
                                              value='Ingrese los términos deseados en el cuadro de arriba',
                                              readOnly=True,
                                              style={'width': '100%', 'font-size': '1.5em'},
                                              ),
                                 dash_table.DataTable(
                                     id='lista-códigos',
                                     editable=False,
                                     row_deletable=False,
                                     filter_action='native',
                                     columns=[
                                         {'name': 'Código', 'id': 'codigo'},
                                         {'name': 'Ruta', 'id': 'DESCRIPCION'},
                                         {'name': 'Descripción', 'id': 'descripcion'},
                                         {'name': 'Unidad', 'id': 'Unidad'},
                                         {'name': 'Medida', 'id': 'Medida'},
                                         {'name': 'Periodicidad', 'id': 'periodo'}
                                     ]
                                 )
                             ],
                             ), #final tab 'Buscar'
                     dcc.Tab(label='¿Quién?',
                             children=[
                                 dcc.Input(
                                     id='quién-es-código',
                                     placeholder='Código...',
                                     value='',
                                     style={'padding': 10, 'width': '10%'}
                                 ),
                                 html.Button('Buscar', id='quién-button', n_clicks=0),
                                 html.Div(
                                     children=[
                                         html.H4('Ubicación de cuenta en el catálogo'),
                                         dcc.Textarea(id='quién',
                                                      value='',
                                                      readOnly=True,
                                                      style={'width': '100%', 'font-size': '1.25em', 'height': 300},)
                                     ],
                                     style={'width': '80%'}
                                 ),
                                 html.Div(
                                     children=[
                                         html.H4('Subcuentas en el catálogo'),
                                         dcc.Textarea(id='subcuentas',
                                                      value='',
                                                      readOnly=True,
                                                      style={'width': '100%', 'font-size': '1.25em', 'height': 300},)
                                     ],
                                     style={'width': '80%'}
                                 ),
                             ],
                     ), # final tab 'INFO'
                     dcc.Tab(label='Ayuda',
                             children=[
                                 dcc.Markdown(ayuda)
                             ],
                             ), #final tab 'Trend'
                     ]
                 )
        ],
        style={'width': '80%','float': 'right', 'display': 'inline-block'}
    ) # fin panel gráfico
    ]
) # fin app layout


@app.callback(
    Output('seleccionar-indicadores', 'data'),
    Input('agregar-codigo-button', 'n_clicks'),
    State('seleccionar-indicadores', 'data'),
    State('seleccionar-indicadores', 'columns'))
def add_row(n_clicks, rows, columns):
    if n_clicks > 0:
        rows.append({c['id']: '' for c in columns})
    return rows


@app.callback(
    Output('seleccionar-indicadores', 'columns'),
    State('adding-rows-name', 'value'),
    State('seleccionar-indicadores', 'columns'))
def update_columns(value, existing_columns):
    existing_columns.append({
        'id': value, 'name': value,
        'renamable': True, 'deletable': True
    })
    return existing_columns



# FUNCIÓN PARA CONSULTAR QUIÉN ES UNA CUENTA
@app.callback(
    Output('quién', 'value'),
    Output('subcuentas', 'value'),
    Input('quién-button', 'n_clicks'),
    State('quién-es-código', 'value'),
)
def quién_subcuentas(n_clicks, código):

    if código in SW.indicadores.index:

        with io.StringIO() as buf, redirect_stdout(buf):
            SW.quien(código)
            quien = buf.getvalue()

        with io.StringIO() as buf, redirect_stdout(buf):
            SW.subcuentas(código)
            subcuentas = buf.getvalue()
    elif código == '':
        quien = subcuentas = f'Escriba el código deseado en el espacio de arriba.'
    else:
        msg = f'El código {código} no aparece en el catálogo de cuentas.'
        msg += '\n\nEsto puede deberse a que: \n\t1. no exista, o \n\t2. el catálogo de este paquete esté desactualizado.'
        quien = subcuentas = msg

    return quien, subcuentas





# FUNCIÓN PARA CONSULTAR EL CATÁLOGO (Buscar códigos)
@app.callback(
    Output('lista-códigos', 'data'),
    Output('buscar-mensaje', 'value'),
    Input('buscar-códigos-button', 'n_clicks'),
    State('buscar-códigos', 'value'),
    State('tipo-búsqueda', 'value'),
)
def mostrar_códigos(n_clicks, frase, tipo):

    if frase:
        # Acomodar la lista de indicadores
        resultados = SW.buscar(**{tipo: frase})

        # Acomodar los datos descargados como un diccionario, para que lo lea dash
        tabla = resultados.reset_index().to_dict(orient='records')
        nrecords = resultados.shape[0]
        msg = f"Hay {nrecords} indicadores que satisface{'n' if nrecords > 1 else ''} su búsqueda." if nrecords \
            else 'No se encontró ningún indicador; intente la búsqueda con otros términos.'

        # dar los resultados
        return tabla, msg
    else:
        msg = "Para buscar indicadores escriba los términos deseados en el espacio proporcionado."
        return [], msg



# FUNCIÓN PARA DESCARGAR LOS DATOS DEL BCCR (Datos y Gráfico)
@app.callback(
    Output('gráfico-datos', 'figure'),
    Output('datos-descargados', 'columns'),
    Output('datos-descargados', 'data'),
    Input('consultar-datos-button', 'n_clicks'),
    State('seleccionar-indicadores', 'data'),
    State('fecha-primera-observación', 'date'),
    State('fecha-última-observación', 'date'),
    State('frecuencia', 'value'),
    State('func', 'value'),
    State('fillna', 'value'),
)
def display_output(n_clicks, rows, FechaInicio, FechaFinal, freq, func, fillna):

    print(type(func))

    # Acomodar la lista de indicadores
    indicadores = dict()
    for item in rows:
        indicadores[item['nombre']] = item['código']

    # Descargar los datos del BCCR
    datos = SW(FechaInicio=FechaInicio, FechaFinal=FechaFinal, **indicadores)

    # Hacer la figura
    fig = px.line(datos, y=datos.columns)

    # Cambiar índice para mostrarlo bien en la tabla
    datos.index = datos.index.to_period().astype(str)

    # Especificar las columnas de la tabla
    columns = [{'name': 'Fecha', 'id': 'fecha' ,'deletable': False, 'renamable': False}]
    columns += [{'name': col, 'id': col ,'deletable': False, 'renamable': False} for col in datos]

    # Acomodar los datos descargados como un diccionario, para que lo lea dash
    tabla = datos.reset_index().to_dict(orient='records')

    # dar los resultados
    return fig, columns, tabla


if __name__ == '__main__':
    app.run_server(debug=True)