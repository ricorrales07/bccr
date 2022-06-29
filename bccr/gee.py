"""
gee: Un módulo para definir la clase ServicioWeb

Este módulo defile la clase ServicioWeb y crea una instancia de la misma, SW. Esta clase permite descargar datos
del ServicioWeb del Banco Central de Costa Rica (https://www.bccr.fi.cr/indicadores-economicos/servicio-web) .

La forma usual de utilizar esta clase es

    >>> from bccr import SW

    * para buscar el código de algún indicador de interés, utilice

    >>> SW.buscar("nombre de un indicador")

    * para saber más detalles del indicador 3541 (por ejemplo)

    >>> SW.quien(3541)

    * para buscar las subcuentas de un indicador, digamos el 779

    >>> SW.subcuentas(779)

    * para descargar datos de indicadors 3, 4 y 22 (por ejemplo), hay varias formas de hacerlo

    >>> SW(indicA=4, indicB=7, indicC=231) # pasando los códigos como valores de parámetros, en
            cuyo caso los indicadores son renombrados como 'indicA', 'indicB' y 'indicC', respectivamente.
    >>> SW(3, 4, 22)   # pasando los códigos directamente (no recomendado)
"""



import pandas as pd
import numpy as np
from anytree import Node, RenderTree
import requests
import os
from dataclasses import dataclass, field
from datetime import datetime
from bs4 import BeautifulSoup
from numpy import nan
import re
from .utils import parse_date_parameter, infer_frequency

import warnings

BCCR_FOLDER = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(BCCR_FOLDER, 'data')
PICKLE_FILE = os.path.join(DATA_FOLDER, 'indicadores.pkl')
EXCEL_FILE =  os.path.join(DATA_FOLDER, 'Indicadores.xlsx')



#: dict of functions: Diccionario que mapea nombres de funciones a objetos de función. Se utilizan para cambiar de
#: frecuencia los datos
FUNCS = {
    'mean': lambda df: np.mean(df.values),
    'sum': lambda df: np.sum(df.values),
    'last': lambda df: df.iloc[-1],
    'first': lambda df: df.iloc[0],
    'nanmean': np.nanmean,
    'nansum': np.nansum,
    'nanlast': lambda df: df.loc[df.last_valid_index()],
    'nanfirst': lambda df: df.loc[df.first_valid_index()],
}




#TODO: Arreglar problema de fechas duplicadas! ejemplo monex 3223 en 2010
#TODO: Arreglar missing values mal codificados! ejemplo monex 3223 aparecen 0s en vez de missing values


@dataclass
class ServicioWeb:
    """
    Una clase para descargar datos del servicio web del Banco Central de Costa Rica

    Attributes
    ----------
    nombre : str
        El nombre del usuario registrado en el servicio web del BCCR
    correo : str
        El correo electrónico registrado por el usuario en el servicio web.
    token : str
        El token recibido por el usuario de parte del BCCR para tener acceso al servicio web.
    indicadores : pd.DataFrame
        una table con la descripción de los indicadores disponibles en el servicio web.

    Examples
    --------
    Asumiendo que Ratón Pérez se registró en el servicio web del BCCR:

    >>> from bccr import ServicioWeb
    >>> consulta = ServicioWeb('Ratón Pérez', 'raton.perez@correo.com', '4SDLJUHKEZ')

    Si Ratón Pérez no se ha registrado en el servicio web del BCCR, entonces simplemente puede usar una instancia
    predeterminada de `ServicioWeb`, llamada `SW`, que utiliza las credenciales del paquete:

    >>> from bccr import SW

    """
    nombre: str
    correo: str
    token: str
    indicadores: pd.DataFrame

    def __usuario__(self):
        """Credenciales de usuario

        Para uso interno de la clase, en la función __descargar__.

        Returns
        -------
        dict
            el nombre, correo, y token en un diccionario con keywords Nombre, CorreoElectronico, y Token
        """
        return dict(Nombre=self.nombre, CorreoElectronico=self.correo, Token=self.token)

    def __observacion__(self, obs):
        """Extraer código de variable, fecha y valor de una observación

        Toma un elemento XML leído por BeautifulSoup y extrae los campos necesarios para identificar una observación.
        Para uso interno de la clase, en la función __descargar__.

        Parameters
        ----------
        obs: nodo de BeautifulSoup
            Representa una observación extraída de un archivo XML descargado del BCCR.

        Returns
        -------
        codigo : str
            el código del indicador
        fecha : str
            la fecha de la observación
        valor : float
            el valor de la observación
        """
        CODIGO = obs.find('COD_INDICADORINTERNO').text
        FECHA = obs.find('DES_FECHA').text[:10]
        VALOR = float(obs.find('NUM_VALOR').text) if obs.find('NUM_VALOR') else nan
        return CODIGO, FECHA, VALOR

    def __descargar__(self, Indicador, FechaInicio=None, FechaFinal=None):
        """Descargar datos del Servicio Web del BCCR

        Construye una consulta por método GET a partir de los parámetros proporcionados. Descarga los datos
        y los transforma en una tabla de datos de Pandas.
        Para uso interno de la clase, para la función datos.

        Parameters
        ----------
        Indicador : str or int
            número del indicador a descargar.
        FechaInicio : int or str, optional
            fecha de la primera observación a descargar,
            int -> año, o str -> yyyy/mm/dd (valor predeterminado es '1900/01/01')
        FechaFinal : str, optional
            fecha de la última observación a descargar, formato dd/mm/yyyy (valor predeterminado es fecha del sistema)

        Returns
        -------
        pd.Series
            Los datos solicitados, indexados por la fecha reportada por el BCCR
        """
        params = self.__usuario__()
        params['Indicador'] = Indicador
        params['FechaInicio'] = parse_date_parameter(FechaInicio, inicio=True, año_primero=False) if FechaInicio else '01/01/1900'
        params['FechaFinal'] = parse_date_parameter(FechaFinal, inicio=False, año_primero=False) if FechaFinal else datetime.now().strftime(
            '%d/%m/%Y')
        params['SubNiveles'] = 'N'


        host = 'https://gee.bccr.fi.cr/Indicadores/Suscripciones/WS/wsindicadoreseconomicos.asmx/ObtenerIndicadoresEconomicos'
        resp = requests.get(host, params)
        error_msg = f'\nNo se obtuvieron datos de indicador {Indicador}. Servidor respondio con mensaje {resp.reason}\n'
        error_msg += "Revise que este indicador efectivamente existe, o intente de nuevo la obtención de los datos."


        if resp.status_code == 200:  # datos recibidos exitosamente
            rawdata = resp.text
            soup = BeautifulSoup(rawdata, 'xml')
            observaciones = soup.find_all('INGC011_CAT_INDICADORECONOMIC')
            if observaciones:
                datos = [self.__observacion__(y) for y in observaciones]
                datos = pd.DataFrame(datos, columns=['variable', 'fecha', 'valor'])

                datos.index = pd.to_datetime(datos.fecha, format="%Y-%m-%d")
                return datos['valor']

            print(error_msg)
        else:
            print(error_msg)
        return None

    def __buscar_frase__(self, frase):
        """Busca indicadores cuya descripción contenga la frase indicada

        Parameters
        ----------
        frase : str
            texto que debe estar presente en la descripción del indicador

        Returns
        -------
        pd.DataFrame
            listado de indicadores que satisfacen la condición
        """
        CAMPOS = ['DESCRIPCION', 'descripcion']
        return pd.DataFrame([self.indicadores[campo].str.contains(frase, case=False) for campo in CAMPOS]).any()

    def buscar(self, todos=None, *, frase=None, algunos=None, frecuencia=None, Unidad=None, Medida=None, periodo=None):

        """buscar códigos de indicadores según su descripción

        Parameters
        ----------
        frase, todos, algunos : str
            texto que debe aparecer en la descripción del indicador. Sólo una de estos tres parámetros debe utilizarse
            a la vez. 'frase' busca una coincidencia exacta, 'todos' que todas las palabras aparezcan (en cualquier
            orden), 'algunos' que al menos una de las palabras aparezca. La búsqueda no es sensible a mayúscula/minúscula.
            Si no se indica un parámetro [por ejemplo, SW.buscar('precios consumidor')], se asume que
            SW.buscar(todos='precio consumidor')
        frecuencia : str, optional. uno de ('A','6M','Q','M','W','D')
            mostrar solo indicadores que tengan la frecuencia indicada.
        Unidad : str, optional
            mostrar solo indicadores que tengan la unidad indicada
        Medida : str, optional
            mostrar solo indicadores que tengan la medida indicada
        periodo: str, optional
            mostrar solo indicadores que tengan la periodicidad indicada

        Returns
        -------
        pd.DataFrame

        Examples
        --------

        Para buscar un indicador que tenga todas las palabras "IMAE", "tendencia", "ciclo" (en cualquier orden)

        >>> from bccr import SW
        >>> SW.buscar("IMAE tendencia ciclo")

        Para buscar un indicador que tenga la frase exacta "Índice de Precios al Consumidor"

        >>> SW.buscar(frase="Índice de Precios al Consumidor")

        Para buscar un indicador que tenga al menos una de las palabras "exportaciones" e "importaciones"

        >>> SW.buscar(algunos="exportaciones importaciones")

        Para buscar los términos "precios transables", y filtrar que muestre solo resultados con medida "Variación interanual"

        >>> SW.buscar('precios transables', Medida='Variación interanual')

        Para mostrar un breve mensaje de ayuda

        >>> SW.buscar()


        Notes
        -----
        El parámetro 'frecuencia' será discontinuado en algún momento. Se recomienda usar el parámetro 'periodo' para
        cumplir la misma funcionalidad.
        """
        CAMPOS = ['DESCRIPCION', 'descripcion', 'Unidad','Medida','periodo']

        if frase:
            temp = self.__buscar_frase__(frase)
        elif todos:
            temp = pd.DataFrame([self.__buscar_frase__(palabra) for palabra in todos.split(' ')]).all()
        elif algunos:
            temp = pd.DataFrame([self.__buscar_frase__(palabra) for palabra in algunos.split(' ')]).any()
        else:
            ayuda = """ BUSCAR
            Esta función ayuda a buscar los códigos de indicadores, utilizando palabras descriptivas.
            Exactamente un parámetro de [frase, todos, algunos] debe ser proporcionado.
            
            Ejemplos de uso:
                buscar("descripción contiene todos estos términos en cualquir orden")
                buscar(frase="descripción contiene esta frase literalmente")
                buscar(algunos="descripción contiene alguno de estos términos")
                buscar()  # muestra este mensaje de ayuda
            """
            print(ayuda)
            return
        results = self.indicadores[temp].copy()

        if frecuencia:
            freq = frecuencia[0].upper()
            results.query('freq == @freq', inplace=True)
        if Unidad:
            results.query('Unidad == @Unidad', inplace=True)
        if Medida:
            results.query('Medida == @Medida', inplace=True)
        if periodo:
            results.query('periodo == @periodo', inplace=True)

        return results[CAMPOS]


    def __actualizar_catalogo__(self):
        """Actualiza el catálago de indicadores

        Returns
        -------
        pd.DataFrame
            el catálogo actualizado

        Notes
        -----
        Esta función es  para uso interno del paquete. Asume la existencia de un archivo de Excel con el catálogo, e
        intenta añadirlo al paquete para futura referencia.

        """
        FREQ = {'Anual': 'A',
                'Mensual': 'M',
                'Trimestral': 'Q',
                'Nueva semanal': 'W',
                'Diaria': 'D',
                'Semestral': '6M',
                'Semanal': 'W'}


        CAMPOS = {'INGC011_COD_INDICADORECONOMIC': 'codigo',
                  'INGC011_COD_INDICADORINTERNO': 'cuenta',
                  'INGC011_NOM_INDICECONOMICOESP': 'nombre',
                  'INGC011_DES_TITULOESPANOL': 'descripcion',
                  'INGC012_COD_MEDIDA': 'medida',
                  'INGC025_COD_UNIDAD': 'unidad',
                  'Periodicidad': 'periodo'}

        unidades = pd.read_excel(EXCEL_FILE, 'INGC012_COD_MEDIDA', dtype=str)
        unidades = unidades.set_index('CodUnidad')['NomUnidadespanol']
        medidas = pd.read_excel(EXCEL_FILE, 'INGC025_COD_UNIDAD', dtype=str)
        medidas = medidas.set_index('Codigo')['NombreEspannol']

        indicadores = pd.read_excel(EXCEL_FILE, 'Indicadores', dtype=str).rename(columns=CAMPOS)
        indicadores['Unidad'] = indicadores['unidad'].map(unidades)
        indicadores['Medida'] = indicadores['medida'].map(medidas)
        indicadores['freq'] = indicadores['periodo'].map(pd.Series(FREQ))
        indicadores['freq'] = indicadores['freq'].astype('category').cat.set_categories(['A', '6M', 'Q', 'M', 'W', 'D'], ordered=True)

        for campo in indicadores:
            indicadores[campo] = indicadores[campo].str.strip()

        indicadores.set_index('codigo', inplace=True)
        indicadores['familia'] = indicadores['cuenta'].str[28:]


        FAMILIAS = indicadores['familia'].value_counts()
        todo = pd.concat([self.__hacer_arbol__(ff, indicadores) for ff in FAMILIAS.index], keys=FAMILIAS.index)
        todo.index = todo.index.get_level_values(1) + '.' + todo.index.get_level_values(0)
        todo.sort_index(inplace=True)

        indicadores = indicadores.merge(todo[['node']], left_on='cuenta', right_index=True)

        indicadores['DESCRIPCION'] = indicadores['node'].astype(str)

        self.indicadores = indicadores
        try:
            indicadores.to_pickle(PICKLE_FILE)
        except:
            print('La tabla indicadores fue actualizada en el objeto, pero no en el paquete bccr.')

    def __hacer_arbol__(self, familia, indicadores):
        """Representa un indicador como parte de un subconjunto de indicadores

        Parameters
        ----------
        familia : str
            código de un indicador en el esquema de cuentas
        indicadores : pd.DataFrame
            tabla con el catálogo de indicadores

        Returns
        -------
        pd.DataFrame
            listado de las cuentas
        """
        grupos = pd.DataFrame(
            dict(nombre=['BCCR', 'Índices de Precios', 'Tipos de cambio', 'Tasas de interés', 'Sector Real',
                         'Sector Externo', 'Sector Fiscal', 'Sector Monetario y Financiero',
                         'Mercados de Negociación', 'Demográficas y Mercado Laboral', 'Expectativas'],
                 codigo=['***'] * 11,
                 cuenta=[f'E{k:02}.00.00.00.00.00.00.00.00' for k in range(11)]))

        def find_parent(cta, catalogo):
            subctas = cta.split('.')
            k = ((np.array(subctas) != "00") * np.arange(9)).max()
            subctas[k] = '00' if k else 'E00'
            cta1 = '.'.join(subctas)
            return cta1 if cta1 in catalogo.index else find_parent(cta1, catalogo)


        filas = indicadores['cuenta'].str.endswith(familia)
        ind = indicadores[filas].reset_index()[['nombre', 'codigo', 'cuenta']]
        ind['cuenta'] = ind['cuenta'].str[:-len(familia) - 1]
        ind = ind.append(grupos, sort=True)
        ind.index = ind['cuenta']
        ind.sort_index(inplace=True)
        ind['parent'] = ind['cuenta'].apply(find_parent, args=(ind['cuenta'],))
        ind.loc['E00.00.00.00.00.00.00.00.00', 'node'] = Node('BCCR')
        for cuenta, (nombre, parent, codigo) in ind[['nombre', 'parent', 'codigo']].iloc[1:].iterrows():
            cdg = '' if codigo == '***' else f' [{codigo}]'
            ind.loc[cuenta, 'node'] = Node(name=nombre + cdg, parent=ind.loc[parent, 'node'])
        ind.drop(grupos['cuenta'], inplace=True)
        return ind


    def __print_node__(self,node):
        """Imprime un árbol que representa la posición de un nodo en el esquema de cuentas.

        Para uso interno de la clase.

        Parameters
        ----------
        node: Node (anytree)
            indicador que se quiere representar, como un nodo del catálogo de indicadores
        Returns
        -------
        None :
            El resultado se imprime a pantalla
        """
        lista = str(node)[12:-1].split('/')
        for i, n in enumerate(lista):
            print('|' + '-' * (3 * (i + 1)) + ' ' + n)

    def quien(self, codigo):
        """Imprime información acerca de un indicador

        Parameters
        ----------
        codigo : str or int
            código numérico del indicador que se desea describir.

        Returns
        -------
        None :
            El resultado se imprime a pantalla

        Examples
        --------
        >>> from bccr import SW
        >>> SW.quien(33438)
        """
        if str(codigo) not in self.indicadores.index:
            print(f'La variable {codigo} no aparece en la lista de indicadores.')
            print('Puede ser que esta variable sí exista en la base de datos del BCCR.')
            return

        A = self.indicadores.loc[str(codigo)]

        ind = self.__hacer_arbol__(A['cuenta'][28:], self.indicadores)
        print(f"Variable {codigo} >>>")
        print(f"   Nombre      : {A['nombre']}.")
        print(f"   Descripcion : {A['descripcion']}.")
        print(f"   Unidad      : {A['Unidad']}" + (f" ({A['Medida']})." if int(A['medida']) > 2 else "."))
        print(f"   Periodicidad: {A['periodo']}.\n")
        self.__print_node__(ind.loc[A['cuenta'][:27]].node)
        print('\n')


    def __nombre__(self, codigo):
        """
        Nombre del indicador con ese código en el catálogo. Si no existe, entonces el código mismo
        Parameters
        ----------
        codigo int or str, código del indicador

        Returns
        -------
        str
        """
        codigo = str(codigo)
        return self.indicadores.loc[codigo, 'nombre'] if codigo in self.indicadores.index else codigo

    def __frecuencia__(self, codigo, serie):
        """
        Frecuencia del indicador codigo. Si existe en el catálogo del paquete, usa el catálogo. De lo contrario, lo
        infiere a partir del índice de los datos
        Parameters
        ----------
        codigo int or str, código del indicador
        serie pd.Series, datos indexados como serie de tiempo para inferir su frecuencia.

        Returns
        -------
            str
        """
        if codigo in self.indicadores.index:
            return self.indicadores.loc[codigo, 'freq']
        else:
            return infer_frequency(serie)


    def subcuentas(self, codigo, arbol=True):
        """Subcuentas de un indicador

        Algunos indicadores pueden desagregarse (por ejemplo, el IMAE total se puede desagregar por actividad económica).
        Esta función ayuda a encontrar los códigos de esas subcuentas.

        Parameters
        ----------
        codigo : str or int
            código numérico del indicador del que se desea conocer sus subcuentas.
        arbol: bool, (=True, opcional)
            Imprime árbol de subcuentas si True.

        Returns
        -------
        list:
            Los códigos de las subcuentas.
            Además, el resultado se imprime a pantalla como un árbol de cuentas (si arbol=True).

        Examples
        --------
        >>> from bccr import SW
        >>> SW.subcuentas(33439)
        """
        cta = self.indicadores.loc[str(codigo), 'node']
        treestr = RenderTree(cta).by_attr()
        if arbol:
            print(treestr)
        
        return re.findall('\[([0-9]+)\]', treestr)

    def datos(self, *codigos, FechaInicio=None, FechaFinal=None, func=None, freq=None, fillna=None, **indicadores):
        """

        Parameters
        ----------
        codigos: sucesión de enteros o strings
                Los códigos numéricos (como int o str) de los indicadores que se desean descargar (ver parámetro
                `indicadores`). En el resultado, el indicador se identifica con el nombre que tiene en el catálogo de
                cuentas; en caso de querer indicar un nombre distinto, solicitar el indicador usando el parámetro
                `indicadores`.
        FechaInicio : str or int, optional
            fecha de la primera observación a descargar. Ver nota 6 abajo para más detalles.
        FechaFinal : str or int, optional
            fecha de la última observación a descargar. Ver nota 6 abajo para más detalles.
        func : str
            Una opción de ['mean', 'sum', 'last', 'first', 'nanmean', 'nansum', 'nanlast', 'nanfirst'].
            función que se desea utilizar para transformar la frecuencia de los datos (predeterminado: None).
            Si se especifica una sola función, se usa la misma para todas las series que lo requiera. Para usar funciones
            distintas puede pasar un diccionario {nombre-de-la-serie: funcion-a-usar,...}
        freq : str, optional
            frecuencia a la que se quiere convertir los datos. Si este parámetro no se indica y se requieren series de
            distintas frecuencias, el resultado será un Data.Frame con la menor periodicidad de las series solicitadas.
        fillna : str, one of ('backfill', 'bfill', 'pad', 'ffill').
            Si hay datos faltantes (por ejemplo, fines de semana), cómo rellenar esos valores. 'backfill' y 'bfill' usan
             el siguiente valor disponible (llena hacia atrás) mientras que 'pad' y 'ffill' usan el último valor
             disponible (llena hacia adelante).
        indicadores: pares de nombre=codigo, de las series requeridas
             Este es el método preferible para indicar las series requeridas (en vez del parámetro `códigos`). Las series
             se enumeran como pares de nombre=codigo, donde nombre es el nombre que tendrá el indicador en el DataFrame
             resultante, y codigo es un número entero que identifica la serie en el servicio web del BCCR.

        Returns
        -------
        pd.DataFrame
            una tabla con los datos solicitados, filas indexadas por tiempo, cada columna es un indicador.

        Notes
        -----
        1. Esta función construye una consulta por método GET a partir de los parámetros proporcionados, para cada uno de
        los Indicadores solicitados. Descarga los datos, los transforma en una tabla de datos de Pandas.

        2. Si hay indicadores de distintas frecuecias, los transforma a la misma frecuencia según el método indicado.

        3. A excepción de `codigos`, todos los parámetros deben usar palabra clave, aunque es preferible usar `indicadores`
        en vez de `codigos`. (Ver los ejemplos)

        4. Hay varias maneras de indicar los Indicadores: (a) simplemente enumerándolos, (b) en una lista o tupla, y
        (c) en un diccionario (método obsoleto, es mejor usar el parámetro `indicadores`). En caso de tratarse de
        diccionario, los códigos se indican como las llaves del diccionario, mientras que los valores del diccionario
        se usan para renombrar las columnas resultantes.

        5. Las instancias de la clase ServicioWeb son ejecutables: si se llaman como una función, simplemente ejecutan la
        función datos()

        6. El formato de fechas es muy flexible. Por ejemplo, todas estas expresiones son válidas:

        - Para indicar el año 2015: se puede emplear tanto un `int` como un `str`

        >>>   FechaInicio = 2015 # se interpreta como  1 de enero de 2015
        >>>   FechaFinal = "2015"  # se interpreta como 31 de diciembre de 2015

        - Para indicar el mes marzo de 2017: cualquiera de estas expresiones es válida

         >>> "2017-03"
         >>> "2017/03"
         >>> "2017m3"
         >>> "03/2017"
         >>> "03-2017"

         En `FechaInicio=` resulta en 1 de marzo de 2017, en `FechaFinal=` resulta en 31 de marzo de 2017.

        - Para indicar el 12 de agosto de 2018:

         >>> "2017/8/12"
         >>> "2017-08-12"
         >>> "12/8/2017"

        Observe que para separar los componentes de una fecha se puede usar cualquier caracter no numérico (usualmente `/` o `-`).

        Examples
        --------
        La forma preferible de solicitar los indicadores es como pares de `nombre=código`, de manera que `nombre` se utilice
        como encabezado de columna en la tabla de datos resultante:

        >>> from bccr import SW
        >>> SW(IMAE=35449, Inflación=25485)

        Para hacer consultas rápidas, puede simplemente pasarse únicamente los códigos

        >>> SW(35449, 25485)

        Observe que si se "ejecuta" la instancia `SW`, simplemente se está ejecutando la función `datos`. Por ello, no es
        necesario escribir `datos` en los ejemplos anteriores

        >>> SW.datos(35449, 25485) # resultado idéntico al anterior, pero digitando más.

        Si se desea, los códigos pueden escribirse como de tipo `str`:

        >>> SW('35449', '25485')

        Puede también pasarse los códigos en un diccionario. **Advertencia** Esta forma se considera obsoleta, pero se mantiene
        aún en el paquete para darle soporte a código escrito con versiones anteriores de `bccr`. Nótese que en esta forma, las
        llaves del diccionario son los códigos, y los valores se usan como encabezado de columna:

        >>> cuentas = {33439:'PIB', 33448:'Consumo', 33451:'Gasto', 33457:'Inversión'}
        >>> SW(cuentas)    # esta forma es obsoleta, será eliminada en una versión futura

        Si desea usar diccionarios, la forma preferible de hacer la consulta anterior es (observe cambio de orden en diccionario
        y que debe desempacarlo con dos asteriscos ** ):

        >>> cuentas = {'PIB': 33439, 'Consumo': 33448, 'Gasto': 33451, 'Inversión':33457}
        >>> SW(**cuentas)    # es necesario usar ** delante del nombre del diccionario
        >>> SW(PIB=33439, Consumo=33448, Gasto=33451, Inversión=33457)  # equivalente a las dos líneas anteriores

        Es posible restringir el rango de los datos, usando los parámetros `FechaInicio=` y `FechaFinal=`:

        >>> SW(IMAE=35449, Inflación=25485, FechaInicio='2000/01/01')

        En caso de solo señalar el año, se sobrentiende "1 de enero" en el caso de `FechaInicio=` y "31 de diciembre" en `FechaFinal=`

        >>> SW(IMAE=35449, Inflación=25485, FechaInicio=2000, FechaFinal=2015)

        Si se solicitan indicadores que tienen distinta periodicidad, el resultado tendrá la periodicidad del indicador menos frecuente.
        Para ello, se puede indicar la función para convertir los datos de mayor a menor frecuencia, y si de seben rellenar datos
        faltantes (por ejemplo, valores faltantes en los fines de semana se pueden intrapolar con el dato del lunes siguiente o
        del viernes anterior)

        >>> SW(IMAE=35449, Inflación=25485, TPM=3541, func='mean', fillna='ffill') # IMAE e Inflación son series mensuales,
        >>> # miestras que TPM es diaria. TPM se convierte en mensual calculando el promedio, habiendo sustituido los
        >>> # valores faltantes con el último dato disponible
        """

        msg = """
        En una futura versión, los indicadores deberán ser solicitados como pares de 'nombre=codigo', o bien 
        como un listado de enteros. Por ejemplo
            SW(TPM=3541, IMAE=913, Inflación=25485)
        o bien
            SW(3541, 913, 25485)                
        """
        for indic in codigos:
            if isinstance(indic, dict):
                warnings.warn(msg)
                for key, value in indic.items():
                    indicadores[value] = key
            elif isinstance(indic, str) or isinstance(indic, int):
                indicadores[self.__nombre__(indic)] = indic
            elif hasattr(indic, '__iter__'):
                warnings.warn(msg)
                for val in indic:
                    indicadores[self.__nombre__(val)] = val
            else:
                raise('No sé cómo interpretar el indicador requerido')

        # Convertir numeros de cuadros a textos
        indicadores = {nombre: str(codigo)  for nombre, codigo in indicadores.items()}


        # Descargar los datos
        datos = {nombre: self.__descargar__(codigo, FechaInicio, FechaFinal) for nombre, codigo in indicadores.items()}

        # Desechar campos de indicadores no descargados
        datos = {nombre: df for nombre, df in datos.items() if df is not None}

        if len(datos) == 0:  # no se encontró ninguna serie, devolver DataFrame vacío.
            return pd.DataFrame(columns=indicadores.keys())


        # LLenar los espacios en blanco en la línea de tiemp
        freqs = {nombre: self.__frecuencia__(codigo, datos[nombre]) for nombre, codigo in indicadores.items() if nombre in datos}
        nfreqs = len(set(freqs.values()))
        datos = {nombre: serie.resample(freqs[nombre]).mean() for nombre, serie in datos.items() if serie is not None}

        if isinstance(fillna, str):
            fillna = fillna.lower()
            if fillna in ('backfill', 'bfill', 'pad', 'ffill'):
                datos = {nombre: serie.fillna(method=fillna) for nombre, serie in datos.items()}
            else:
                warnings.warn("Método de remplazo de valores faltantes debe ser uno de ('backfill', 'bfill', 'pad', 'ffill')")
        elif fillna is not None:
            warnings.warn("Método de remplazo de valores faltantes debe ser uno de ('backfill', 'bfill', 'pad', 'ffill')")


        # Convertir frecuencias, si es necesario o requerido
        if nfreqs > 1 or freq:
            freqs2 = pd.Series(freqs).astype('category').cat.set_categories(['A', '6M', 'Q', 'M', 'W', 'D'], ordered=True)
            freq = freq if freq else freqs2.min()
            if func is None:
                msg = """
                En una futura versión, si necesita cambiar la frecuencia de los datos deberá indicar la función a utilizar
                para dicha conversión, ya sea con 'func=nombre_de_funcion' (se aplica esta función a todas las variable que
                requieran cambiar de frecuencia), o bien con un diccionario con claves iguales a los nombres de indicadores
                 (o códigos, si no asigna nombres) y valores iguales a la función a utilizar para ese indicador.
                 
                Utilizando func=numpy.sum para esta conversión. 
                """
                warnings.warn(msg)
                func = np.sum

            if type(func) is str:
                if func not in FUNCS.keys():
                    raise ValueError("El parámetro 'func' debe ser uno de " + str(list(FUNCS.keys())))
                else:
                    funciones = {nombre: FUNCS[func] for nombre in indicadores}
            elif callable(func):
                funciones = {nombre: func for nombre in indicadores}
            else:
                raise ValueError("El parámetro 'func' debe ser un str, función, o diccionario")

            for nombre, serie in datos.items():
                if freqs[nombre] != freq:
                    if serie.isna().any():
                        msg = f"Se detectaron valores faltantes en serie '{nombre}' antes de cambiarle de frecuencia.\n"
                        msg += "Considere completar esos datos usando el parámetro 'fillna' de esta función."
                        warnings.warn(msg)
                    datos[nombre] = serie.resample(freq).apply(funciones[nombre])

        datos = pd.DataFrame(datos)
        datos.index = datos.index.to_period()
        return datos


    def __call__(self, *args, **kwargs):
        return self.datos(*args, **kwargs)

    def __str__(self):
        return "Clase ServicioWeb: permite buscar y descargar datos de indicadores del servicio web del Banco Central de Costa Rica."


    def __repr__(self):
        return self.__str__()

#: bccr.ServicioWeb: Este es un objeto de clase `ServicioWeb` con parámetros de inicialización predeterminados. Puede
#: importarse en una sesión simplemente con `from bccr import SW`.
SW = ServicioWeb(nombre = 'Paquete BCCR Python',
                 correo = 'paquete.bccr.python@outlook.com',
                 token = '5CMRCBTHMT',
                 indicadores = pd.read_pickle(PICKLE_FILE))