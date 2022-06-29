from jupyter_dash import JupyterDash
import pandas as pd
from dash.dependencies import Input, Output, State
from dash import dash_table
from dash import dcc
from dash import html
from dash_extensions import Download
from dash_extensions.snippets import send_data_frame
from dash.dash_table.Format import Format, Scheme
import plotly.express as px
from bccr import SW
import io
from contextlib import redirect_stdout

from datetime import date

import webbrowser

DATOS_PARA_DESCARGAR = [pd.DataFrame()]


# Esta parte controla asuntos de estética de la página
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']



ayuda = """
# Acerca del paquete bccr

## Una API de Python para descargar datos del Banco Central de Costa Rica

El propósito de esta interfase gráfica es facilitar la búsqueda y descarga de indicadores publicados por el [Banco Central de Costa Rica](https://www.bccr.fi.cr/) por medio de su servicio web. 

La interfase está basada en el paquete de Python `bccr` desarrollada por el autor de esta interfase. El paquete ofrece dos clases para buscar datos y descargarlos:

* [`ServicioWeb`](http://randall-romero.com/demo-bccr-servicioweb/): descarga indicadores individuales del [servicio web](https://www.bccr.fi.cr/indicadores-economicos/servicio-web) del Banco Central.
* [`PaginaWeb`](http://randall-romero.com/demo-bccr-paginaweb/): descarga cuadros individuales (algunos con un solo indicador, otros con varios), de la página de [indicadores económicos](https://www.bccr.fi.cr/indicadores-economicos).

En esta versión, la interfase solo permite descargar datos a través del `Servicioweb`. 

Los datos se descargan y se presentan en una tabla en formato *tidy*, en la cual cada fila corresponde a un período (día, mes, trimestre, año) y cada columna a un indicador. 

Este [video de YouTube](https://youtu.be/eB8YCQ-nn1g) contiene un tutorial acerca de cómo utilizar el paquete.
---

## Parámetros de búsqueda (panel izquierdo):
### Indicadores
En esta tabla se indican los códigos de los indicadores que se desean descargar, así como el nombre que se le quiere dar al indicador
en la tabla de datos. Puede agregar indicadores usando el botón "Agregar otro código".

### Rango de fechas a consultar:
Delimita el rango de datos que se descargan. Las fechas se deben indicar en formato yyyy/mm/dd.

### Frecuencia de los datos:
De manera predeterminada se muestran datos en la frecuencia original (si se solicitan indicadores de distinta frecuencia, se 
reportan con la menor de las frecuencias). Se puede especificar una frecuencia menor (por ejemplo, trimestral para datos diarios o mensuales, pero no para datos anuales).

### Función para agregación 
Si se cambia la frecuencia de los datos, esta función determina cómo se agregan los datos de un período (promedio, suma, último o primero). Puede especificar si esta agregación debe propagar o ignorar los valores faltantes. 

### Rellenar datos faltantes
En algunas series es común que hayan brechas en la serie de datos (por ejemplo, en series diarias si no se reporta dato los fines
de semana). Esta opción permite imputar valores a estos datos faltantes (ya sea usando el último dato disponible o el siguiente).
Esta operación se hace antes de la agregación de datos (si se cambia la frecuencia de las series). 

---

## Viñetas
### Datos
Presenta una tabla con los datos descargados. Puede descargar estos datos oprimiendo los botones que aparecen en la parte superior.
Además, en la parte superior de la viñeta aparece el código de Python que descarga los datos mostrados en la tabla.

### Gráfico
Presenta un gráfico de todas las series descargadas. Puede ocultar y volver a mostrar series individuales haciendo clic a su
nombre en la leyenda del gráfico.

### Buscar códigos
Facilita la obtención de los códigos del catálogo de indicadores del Servicio Web. La tabla resultante de buscar un término
(palabra o frases) puede filtrarse escribiendo en la fila superior (por ejemplo, para que solo muestre indicadores como 
porcentaje de variación, o solo indicadores mensuales).

### ¿Quién?
Permite identificar las relaciones de las cuentas, mostrando las cuentas superiores así como las subcuentas, para un código
especificado. Esto sirve, por ejemplo, si de desea descargar los componentes del IPC. 

---

## Acerca del autor
Randall Romero Aguilar, PhD

[randall-romero.com](http://randall-romero.com)

Si desea reportarme un fallo en esta herramienta, o bien sugerirme alguna mejora, por favor escríbame al correo
[randall.romero@outlook.com](mailto:randall.romero@outlook.com)

---

## Aviso importante

Este paquete no es un producto oficial de BCCR. El autor lo provee para facilitar el manejo de datos, pero no ofrece ninguna garantía acerca de su correcto funcionamiento. 
"""




app = JupyterDash(__name__, external_stylesheets=external_stylesheets, prevent_initial_callbacks=True)
app.layout = html.Div([
    html.Div(
        children=[
            html.H2('Indicadores'),
            dash_table.DataTable(
                id='seleccionar-indicadores',
                columns=[
                    {'name': 'Nombre', 'id': 'nombre', 'deletable': False, 'renamable': False},
                    {'name': 'Código', 'id': 'código', 'deletable': False, 'renamable': False},
                ],
                data=[{'nombre': 'nombre_variable', 'código': ''}],
                editable=True,
                row_deletable=True
            ), # fin tabla de códigos a descargar
            html.Button('Agregar otro código', id='agregar-codigo-button', n_clicks=0),
            html.H3('Parámetros opcionales'),
            html.H4('Rango de fechas a consultar'),
            dcc.DatePickerSingle(
                id='fecha-primera-observación',
                display_format='YYYY/MM/DD',
                min_date_allowed=date(1950, 1, 1),
                max_date_allowed=date(2030,12,31),
                initial_visible_month=date(1990, 1, 1),
                date=None #date(1990, 1, 1)
            ), # fin fecha de inicio
            dcc.DatePickerSingle(
                id='fecha-última-observación',
                display_format='YYYY/MM/DD',
                min_date_allowed=date(1950, 1, 1),
                max_date_allowed=date(2030,12,31),
                initial_visible_month=date.today(), #(2021, 1, 1),
                date=None #date.today()
            ), # fin fecha de cierre
            html.H4('Frecuencia de los datos'),
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
            html.H4('Función para agregación'),
            dcc.Dropdown(
                id='func',
                options=[
                    {'label': '  ', 'value': 'None'},
                    {'label': 'Promedio', 'value': 'mean'},
                    {'label': 'Suma', 'value': 'sum'},
                    {'label': 'Último', 'value': 'last'},
                    {'label': 'Primero', 'value': 'first'},
                    {'label': 'Promedio, ignorando NaN', 'value': 'nanmean'},
                    {'label': 'Suma, ignorando NaN', 'value': 'nansum'},
                    {'label': 'Último, ignorando NaN', 'value': 'nanlast'},
                    {'label': 'Primero, ignorando NaN', 'value': 'nanfirst'},
                ],
                value='None'
            ), # fin de función para cambiar frecuencia de los datos
            html.H4('Rellenar datos faltantes'),
            dcc.Dropdown(
                id='fillna',
                options=[
                    {'label': 'No', 'value': 'no'},
                    {'label': 'Usar último disponible', 'value': 'ffill'},
                    {'label': 'Usar próximo disponible', 'value': 'bfill'},
                ],
                value='no'
            ), # fin de función para cambiar frecuencia de los datos
            html.Button('Consultar datos', id='consultar-datos-button', n_clicks=0,
                        style={'width': '80%', 'font-size': '1.25em', 'margin': '40px',
                               'color':'white', 'background-color': 'OrangeRed'}),
            html.Img(src='https://randall-romero.github.io/econometria/_static/r2-logo.png',width='80%', style={'margin-left': '40px'}),
        ],
        style={'width': '20%', 'display': 'inline-block', 'background-color': 'AliceBlue'}
    ), # fin panel controles
    html.Div( children=[
                 dcc.Tabs([
                     # Panel 1: TABLA DE DATOS================================================================
                     dcc.Tab(label='Datos',
                             children=[
                                 dcc.Textarea(id='comando',
                                              value='Acá aparecerá el código que descarga sus datos',
                                              readOnly=True,
                                              style={'width': '100%', 'font-size': '1.5em',
                                                     'color':'white', 'background-color': 'LightSlateGray'},
                                              ),
                                 html.Table(children=[
                                     html.Tr(children=[
                                         html.Td(dcc.Markdown("Para descargar los datos ⇒")),
                                         html.Td(dcc.Input(id='file-name', type='text', value='nombre-de-archivo', size='16')),
                                         html.Td([html.Button("Download Excel", id='btn-xlsx'),
                                                  Download(id="download-dataframe-xlsx")]),
                                         html.Td([html.Button("Download Stata", id='btn-dta'),
                                                  Download(id="download-dataframe-dta")]),
                                         html.Td([html.Button("Download CSV", id='btn-csv'),
                                                  Download(id="download-dataframe-csv")]),
                                     ])
                                 ]),
                                 dash_table.DataTable(
                                     id='datos-descargados',
                                     editable=False,
                                     row_deletable=False,
                                     style_as_list_view=True,
                                 )
                             ],
                             ),
                     # PANEL 2:  GRÁFICO======================================================================
                     dcc.Tab(label='Gráfico',
                             children=[
                                 dcc.Graph(id='gráfico-datos'),
                                 dcc.Markdown(
                                     """
                                     **Nota:** Si los indicadores que descarga tienen una escala numérica muy
                                     distinta, será difícil apreciar algunos de ellos. En este caso puede ocultar
                                     y mostrar indicadores haciendo clic en la leyenda.
                                     """
                                 ),
                             ],
                             ),
                     # PANEL 3: BUSCAR CÓDIGOS================================================================
                     dcc.Tab(label='Buscar códigos',
                             children=[
                                 dcc.Input(
                                     id='buscar-códigos',
                                     placeholder='Escriba acá los términos que desea buscar...',
                                     value='',
                                     style={'padding': 10, 'width': '50%'}
                                 ),
                                 html.Button('Buscar', id='buscar-códigos-button', n_clicks=0),
                                 dcc.RadioItems(
                                     id='tipo-búsqueda',
                                     options=[
                                         {'label': 'frase exacta', 'value': 'frase'},
                                         {'label': 'todas las palabras', 'value': 'todos'},
                                         {'label': 'alguna de las palabras', 'value': 'algunos'}
                                     ],
                                     value='todos',
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
                                     sort_action='native',
                                     style_cell={'textAlign': 'left'},
                                     row_deletable=False,
                                     filter_action='native',
                                     columns=[
                                         {'name': 'Código', 'id': 'codigo'},
                                         #{'name': 'Descripción', 'id': 'descripcion'}, ya no se reporta
                                         {'name': 'Ruta', 'id': 'DESCRIPCION'},
                                         {'name': 'Unidad', 'id': 'Unidad'},
                                         {'name': 'Medida', 'id': 'Medida'},
                                         {'name': 'Periodicidad', 'id': 'periodo'}
                                     ]
                                 )
                             ],
                             ),
                     # PANEL 4: QUIÉN ES ESTE INDICADOR================================================
                     dcc.Tab(label='¿Quién?',
                             children=[
                                 dcc.Markdown("Código de cuenta ⇒"),
                                 dcc.Input(
                                     id='quién-es-código',
                                     placeholder='Código...',
                                     value='',
                                     style={'padding': 10, 'width': '10%'}
                                 ),
                                 dcc.Markdown("Número de subniveles en subcuentas ⇒"),
                                 dcc.Input(
                                     id='profundidad-arbol',
                                     placeholder='(opcional: 1,2,...8)',
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
                     ),
                     # PANEL 5: AYUDA======================================================================
                     dcc.Tab(label='Ayuda',
                             children=[
                                 dcc.Markdown(ayuda)
                             ],
                             ), #final tab 'Trend'
                     ]
                 )
        ],
        style={'width': '80%','float': 'right', 'display': 'inline-block'}
    )
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


# FUNCIÓN PARA CONSULTAR QUIÉN ES UNA CUENTA
@app.callback(
    Output('quién', 'value'),
    Output('subcuentas', 'value'),
    Input('quién-button', 'n_clicks'),
    State('quién-es-código', 'value'),
    State('profundidad-arbol', 'value'),
)
def quién_subcuentas(n_clicks, código, maxlevel):

    if código in SW.indicadores.index:
        maxlevel = int(maxlevel if maxlevel else 9)

        with io.StringIO() as buf, redirect_stdout(buf):
            SW.quien(código)
            quien = buf.getvalue()

        with io.StringIO() as buf, redirect_stdout(buf):
            SW.subcuentas(código, maxlevel=maxlevel)
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



# FUNCIÓN PARA CONSULTAR LOS DATOS DEL BCCR (Datos y Gráfico)
@app.callback(
    Output('gráfico-datos', 'figure'),
    Output('datos-descargados', 'columns'),
    Output('datos-descargados', 'data'),
    Output('comando', 'value'),
    Input('consultar-datos-button', 'n_clicks'),
    State('seleccionar-indicadores', 'data'),
    State('fecha-primera-observación', 'date'),
    State('fecha-última-observación', 'date'),
    State('frecuencia', 'value'),
    State('func', 'value'),
    State('fillna', 'value'),
)
def display_output(n_clicks, rows, FechaInicio, FechaFinal, freq, func, fillna):


    # Acomodar la lista de indicadores
    indicadores = dict()
    for item in rows:
        indicadores[item['nombre']] = item['código']

    # Interpretar parámetros freq y fillna
    if freq == 'O':
        freq = None

    if fillna == 'no':
        fillna = None

    if func == 'None':
        func = None

    # Descargar los datos del BCCR
    #busqueda_str = "from bccr import SW\n"
    if '' in indicadores.values():  # no consultar al BCCR al arrancar
        datos = pd.DataFrame(columns=indicadores.keys())
        busqueda_str = "SW()"
    else:
        busqueda_str = "SW("
        busqueda_str += ', '.join([f'{key}={val}' for key, val in indicadores.items()]) + ', '


        busqueda_str += f"FechaInicio='{FechaInicio}', " if FechaInicio else ""
        busqueda_str += f"FechaFinal='{FechaFinal}', " if FechaFinal else ""
        busqueda_str += f"func='{func}', " if func else ""
        busqueda_str += f"freq='{freq}', " if freq else ""
        busqueda_str += f"fillna='{fillna}')" if fillna else ")"
        busqueda_str = busqueda_str[:-3] + ")" if busqueda_str[-3:] == ', )' else busqueda_str
        datos = SW(FechaInicio=FechaInicio, FechaFinal=FechaFinal, func=func, freq=freq, fillna=fillna, **indicadores)

    DATOS_PARA_DESCARGAR[0] = datos  # para poder descargarlos después

    # Hacer la figura
    if datos.shape[0]:
        fig = px.line(datos, x=datos.index.to_timestamp(), y=datos.columns, height=800)
    else:
        fig = px.line(x=[0], y=[0])

    # Cambiar índice para mostrarlo bien en la tabla
    datos.index = datos.index.astype(str)

    # Especificar las columnas de la tabla
    columns = [{'name': 'Fecha', 'id': 'fecha' ,'deletable': False, 'renamable': False}]
    columns += [{'name': col, 'id': col ,'deletable': False, 'renamable': False, 'type':'numeric', 'format':Format(precision=4, scheme=Scheme.fixed)} for col in datos]

    # Acomodar los datos descargados como un diccionario, para que lo lea dash
    tabla = datos.reset_index().to_dict(orient='records')

    # dar los resultados
    return fig, columns, tabla, busqueda_str


# FUNCIÓN PARA DESCARGAR LOS DATOS COMO ARCHIVOS A LA COMPUTADORA LOCAL
@app.callback(
    Output("download-dataframe-xlsx", "data"),
    Input("btn-xlsx", "n_clicks"),
    State("file-name", "value"),
    prevent_initial_call=True,
)
def descargar_excel(n_clicks, nombre):
    datos = DATOS_PARA_DESCARGAR[0]
    return send_data_frame(datos.to_excel, f"{nombre}.xlsx", sheet_name="datos")


@app.callback(
    Output("download-dataframe-dta", "data"),
    Input("btn-dta", "n_clicks"),
    State("file-name", "value"),
    prevent_initial_call=True,
)
def descargar_stata(n_clicks, nombre):
    datos = DATOS_PARA_DESCARGAR[0]
    return send_data_frame(datos.to_stata, f"{nombre}.dta")


@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn-csv", "n_clicks"),
    State("file-name", "value"),
    prevent_initial_call=True,
)
def descargar_csv(n_clicks, nombre):
    datos = DATOS_PARA_DESCARGAR[0]
    return send_data_frame(datos.to_csv, f"{nombre}.csv")





def GUI(colab=False):
    if colab:
        app.run_server(mode='external')
    else:
        webbrowser.open('http://127.0.0.1:8050/')
        app.run_server(debug=False)


if __name__ == '__main__':
    GUI()