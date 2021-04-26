from dataclasses import dataclass
import pandas as pd
import numpy as np
import os
import time
import warnings
import webbrowser

from .utils import parse_date_parameter
from .scrape import CHARTFREQUENCIES
from .utils import findColumnTitles, fixCommas, is_leap_year
from .fetch import FIRST_OBSERVATION

BCCR_FOLDER = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(BCCR_FOLDER, 'data')
PICKLE_FILE = os.path.join(DATA_FOLDER, 'cuadros.pkl')

FRASE_AYUDA = """
CLASE PaginaWeb

Esta clase permite buscar y descargar cuadros de indicadores del sitio web del Banco Central de Costa Rica.
Suponiendo que el objeto de clase PaginaWeb se llama "consulta":
    * para buscar cuadros, utilice 
        consulta.buscar()
    * para descargar datos de cuadros 4, 7 y 231 (por ejemplo), hay varias formas de hacerlo 
        consulta(4, 7, 231)   # pasando los códigos directamente
        consulta([4, 7, 231]) # pasando los códigos en una lista
        consulta({'4':'indicA', '7':'indicB', '231':'indicC'} # pasando los códigos en un diccionario        
"""

@dataclass
class PaginaWeb:
    cuadros: pd.DataFrame

    def api(self, Cuadro, *, FechaInicio=None, FechaFinal=None, excel=True, abrir=False):
        """
        Construye un URL para obtener datos del sitio de indicadores económicos del BCCR

        Parameters
        ----------
        Cuadro:  int
              Número que identifica el cuadro que desea descargarse del sitio web del BCCR
        FechaInicio : str or int, optional
            fecha de la primera observación a descargar. Ver nota 1 de la función `datos` para detalles de formato.
        FechaFinal : str or int, optional
            fecha de la última observación a descargar. Ver nota 1 de la función `datos` para detalles de formato.
        excel: bool (opcional, predeterminado = True)
            Si `True`, obtiene la versión Excel de los datos, `False` obtiene la versión HTML
        abrir: bool (opcional, predeterminado = True)
            Si `True`, abre la página web indicada por el URL en el navegador de internet predeterminado
        Returns
        -------
            El URL para descargar los datos del cuadro indicado: str

        Examples
        --------
            1. Obtener el URL  del IPC (Cuadro 9)

            >>> from bccr import PW
            >>> PW.api(9)

            'https://gee.bccr.fi.cr/indicadoreseconomicos/Cuadros/frmVerCatCuadro.aspx?CodCuadro=9&Exportar=True&Excel=True'

            2. URL para datos del M1 desde enero de 2010

            >>> PW.api(125, FechaInicio=2010)

            'https://gee.bccr.fi.cr/indicadoreseconomicos/Cuadros/frmVerCatCuadro.aspx?CodCuadro=125&FecInicial=2010/01/01&Exportar=True&Excel=True'

            3. URL para datos del IPC no transable (Cuadro 289) entre 2010 y 2015

            >>> PW.api(289, FechaInicio=2010, FechaFinal=2015)

            'https://gee.bccr.fi.cr/indicadoreseconomicos/Cuadros/frmVerCatCuadro.aspx?CodCuadro=289&FecInicial=2010/01/01&FecFinal=2015/12/31&Exportar=True&Excel=True'

            4. URL para el M1 entre 2010 y 2015, pero en formato HTML (en vez del formato Excel predeterminado)

            >>> PW.api(125, FechaInicio=2010, FechaFinal=2015, excel=False)

            'https://gee.bccr.fi.cr/indicadoreseconomicos/Cuadros/frmVerCatCuadro.aspx?CodCuadro=125&FecInicial=2010/01/01&FecFinal=2015/12/31'

            5. Igual que el anterior, pero usando fechas predeterminadas. La opción `abrir=True` muestra los datos en su navegador de internet predeterminado

            >>> PW.api(125, excel=False, abrir=True)  # opens link in browser

            'https://gee.bccr.fi.cr/indicadoreseconomicos/Cuadros/frmVerCatCuadro.aspx?CodCuadro=125'
        """
        bccr_web = "https://gee.bccr.fi.cr/indicadoreseconomicos/"

        bccr_web += "Cuadros/frmVerCatCuadro.aspx?"
        params = dict(CodCuadro=Cuadro)
        if FechaInicio:
            params['FecInicial'] = parse_date_parameter(FechaInicio, inicio=True, año_primero=True)
        if FechaFinal:
            params['FecFinal'] = parse_date_parameter(FechaFinal, inicio=False, año_primero=True)
        if excel:
            params['Exportar'] = True
            params['Excel'] = True

        bccr_web += "&".join(f"{k}={v}" for k,v in params.items())

        if abrir:
            webbrowser.open(bccr_web)

        return bccr_web

    def web(self, Cuadro):
        """
        Abre el cuadro especificado en el sitio del BCCR, usando el navegador de Internet predeterminado.

        Parameters
        ----------
        Cuadro:  int or str
             Número de cuadro que se desea verificar

        Returns
        -------
            None

        Examples
        --------
        Para abrir el cuadro 125

        >>> self.web(125)
        """

        self.api(Cuadro, excel=False, abrir=True)
        return

    def __downloadChart__(self, chart, first=None, last=None, quiet=False):
        """
            Downloads data from BCCR website.

            This function converts a BCCR html file into a pandas dataframe. Other
            functions take this dataframe and "clean it" to return a tidy dataframe.

        Parameters
        ----------
        chart   : A number identifying the BCCR's data table (integer).
        first   : The first year to download (integer, default=None).
        last    : The last year to download (integer, default=None)
        quiet   : Print download info if False, nothing if True

        Returns
        -------
            data    : A pandas DataFrame with data in the same format as in BCCR website. First column is used to set the
                    (row) index and column headers are use to set the columns property
            title   : Chart title (string)
            subtitle : Chart subtitles (string)

        Examples
        --------
            1. Download data on money supply (M1) for 2011 to 2015

            >>> self.__downloadChart__(125, 2011, 2015)

            2. Same as before, but without printing download info(name of series, url, retrieved date-time)

            >>> self.__downloadChart__(138, 2011, 2015, quiet=True)
        """
        chart_url = self.api(chart, FechaInicio=first, FechaFinal=last,excel=True, abrir=False)
        rawdata = pd.read_html(chart_url, thousands="")[0]
        title, subtitle, subts2 = rawdata.iloc[:3, 0]
        if pd.notnull(subts2):
            subtitle += ' --- %s' % subts2

        rawdata.set_index(0, inplace=True)
        h = findColumnTitles(rawdata)
        rawdata.columns = rawdata.iloc[h]
        rawdata = rawdata.iloc[h + 1:].applymap(fixCommas)

        if not quiet:
            info = 'Descargando el cuadro %s:' % chart
            info += ('\n\t' + title) if title else ''
            info += ('\n\t' + subtitle) if subtitle else ''
            info += '\n\tDescargado el %s desde:' % time.strftime("%c")
            info += '\n\t' + chart_url + '\n'
            print(info)

        rawdata._metadata = {'title': title, 'subtitle': subtitle}
        return rawdata

    def __parse__(self, chart, first=None, last=None, freq=None, func=None, quiet=True):

        # TODO: Add chartFormat='DayIndicator' to the possible options!!! Example chart=572

        chartFormat = self.cuadros.loc[chart, 'chartFormat']

        data = self.__downloadChart__(chart, first, last, quiet)
        title = data._metadata['title']

        ''' CLEAN DATA'''
        if chartFormat == 'MonthYear' and 'total' in str(data.index[0]).lower():
            data.drop(data.index[0], inplace=True)
        elif chartFormat == 'DayYear':
            nonleap = np.array([~is_leap_year(int(y)) for y in data.columns])
            data.iloc[59, nonleap] = np.inf  # row 59 = Feb 29 (counting from zero-base)

        ''' GET FIRST OBSERVATION '''
        try:
            t0 = FIRST_OBSERVATION[chartFormat](data)
        except:
            raise Exception(NotImplemented)

        ''' GET DATA IN TIME v. SERIES FORMAT '''
        if chartFormat in ['IndicatorYear', 'IndicatorQuarter', 'IndicatorMonth', 'MonthYear', 'DayYear']:
            data = data.transpose()

        ''' STACK DATA '''
        if chartFormat in ['YearMonth', 'MonthYear', 'DayYear']:
            data = data.stack(dropna=False)

        ''' REMOVE 29 FEB IN NON-LEAP YEARS '''
        if chartFormat in ['DayYear']:
            data = data[data != np.inf]

        ''' REMOVE 29 REB IN NON-LEAP YEARS'''
        if chartFormat in ['DayIndicator']:
            not_a_leap_year = ~is_leap_year(np.array([int(x.split()[-1]) for x in data.index]))
            feb29 = np.array(['29 Feb' in x for x in data.index])
            wrong_day = feb29 & not_a_leap_year
            data = data.iloc[~wrong_day]

        ''' ADD TIME INDEX '''
        data.index = pd.period_range(start=t0, periods=data.shape[0], freq=CHARTFREQUENCIES[chartFormat][0])

        ''' DROP MISSING VALUES '''
        if isinstance(data, pd.Series):
            data.name = str(chart)
            data.dropna(inplace=True)
        elif isinstance(data, pd.DataFrame):
            data.columns = [str(x) for x in data.columns]
            data = data.dropna(axis=0, how='all').dropna(axis=1, how='all')
        else:
            raise ValueError('Unexpected data type: %s' % type(data))

        ''' RESAMPLE DATA '''
        if freq:
            func = func if func else np.mean
            data = data.resample(freq).apply(func)

        return data

    def soporte(self, cuadro):
        """
        Indica si un `cuadro` específico puede descargarse con PaginaWeb

        Parameters
        ----------
        cuadro: int o str
            Número de cuadro que se desea verificar

        Returns
        -------
            bool

        """
        return int(cuadro) in self.cuadros.index


    def __nombre__(self, cuadro):
        """
        Nombre del indicador con ese código en el catálogo. Si no existe, entonces el código mismo
        Parameters
        ----------
        codigo int or str, código del indicador

        Returns
        -------
        str
        """
        return self.cuadros.loc[cuadro, 'title'] if self.soporte(cuadro) else str(cuadro)


    def datos(self, *Cuadros, FechaInicio=None, FechaFinal=None, func=np.sum, freq=None, info=False, **indicadores):
        """ Descargar datos del sitio de Indicadores Económicos del BCCR

        Construye una consulta por método GET a partir de los parámetros proporcionados, para cada uno de los
        Indicadores solicitados. Descarga los datos, los transforma en una tabla de datos de Pandas.
        Si hay indicadores de distintas frecuecias, los transforma a la misma frecuencia según el método indicado.

        Parameters
        ----------
        Cuadros: sucesión de enteros o strings
                Los códigos numéricos (como int o str) de los cuadros que se desean descargar (ver parámetro
                `indicadores`). En el resultado, el indicador se identifica con el nombre que tiene en el catálogo de
                cuentas; en caso de querer indicar un nombre distinto, solicitar el cuadro usando el parámetro
                `indicadores`
        FechaInicio : str or int, optional
            fecha de la primera observación a descargar. Ver nota 6 abajo para más detalles.
        FechaFinal : str or int, optional
            fecha de la última observación a descargar. Ver nota 6 abajo para más detalles.
        func
        freq : str, optional
            frecuencia a la que se quiere convertir los datos. Si este parámetro no se indica y se requieren series de
            distintas frecuencias, el resultado será un Data.Frame con la menor periodicidad de las series solicitadas.
        info:  bool, optional (default=False)
            Si `True`, se imprime metadata del cuadro descargado, así como un hipervículo para consultar los datos en el
            sitio de Internet del BCCR
        indicadores: pares de nombre=codigo, de los cuadros requeridos
             Este es el método preferible para indicar las series requeridas (en vez del parámetro `Códigos`). Las series
             se enumeran como pares de nombre=codigo, donde nombre es el nombre que tendrá el indicador en el DataFrame
             resultante, y codigo es un número entero que identifica el cuadro en la página de indicadores económicos del BCCR.
        Returns
        -------
        pd.DataFrame
            una tabla con los datos solicitados, filas indexadas por tiempo, cada columna es un indicador.

        Notes
        -----
        1. Esta función construye un URL a partir de los parámetros proporcionados, para cada uno de los Indicadores solicitados.
        Descarga los datos, los transforma en una tabla de datos de Pandas.

        2. Si hay indicadores de distintas frecuecias, los transforma a la misma frecuencia según el método indicado.

        3. A excepción de `*Cuadros`, todos los parámetros deben usar palabra clave, aunque es preferible usar el parámetro
        `indicadores` en vez de `*Cuadros`. (Ver los ejemplos)

        4. Hay varias maneras de indicar los Indicadores: (a) simplemente enumerándolos, (b) en una lista o tupla, y
        (c) en un diccionario (método obsoleto, es mejor usar el parámetro `indicadores`). En caso de tratarse de
        diccionario, los códigos se indican como las llaves del diccionario, mientras que los valores del diccionario
        se usan para renombrar las columnas resultantes.

        5. Las instancias de la clase PaginaWeb son ejecutables: si se llaman como una función, simplemente ejecutan la
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
        La forma preferible de solicitar los indicadores es como pares de `nombre=cuadro`, de manera que `nombre` se utilice
        como encabezado de columna en la tabla de datos resultante:

        >>> from bccr import PW
        >>> SW(M1=125, Npp=177)

        """

        msg = """
        En una futura versión, los indicadores deberán ser solicitados como pares de 'nombre=codigo', o bien 
        como un listado de enteros. Por ejemplo
            PW(M1=125, Npp=177)
        o bien
            PW(125, 177)                
        """


        for indic in Cuadros:
            if isinstance(indic, dict):
                warnings.warn(msg)
                for key, value in indic.items():
                    indicadores[value] = int(key)
            elif isinstance(indic, str) or isinstance(indic, int):
                indicadores[self.__nombre__(indic)] = int(indic)
            elif hasattr(indic, '__iter__'):
                warnings.warn(msg)
                for val in indic:
                    indicadores[self.__nombre__(val)] = int(val)
            else:
                raise('No sé cómo interpretar el indicador requerido')

        indicadores_válidos = dict()
        for nombre, codigo in indicadores.items():
            if self.soporte(codigo):
                indicadores_válidos[nombre] = codigo
            else:
                print(f"PaginaWeb aún no tiene soporte para el cuadro {codigo}, o bien no existe")

        if indicadores_válidos:
            #__parse__(self, chart, first=None, last=None, freq=None, func=None, quiet=True):
            datos = {nombre: self.__parse__(codigo, first=FechaInicio, last=FechaFinal, freq=freq, func=func, quiet=not info) for nombre, codigo in indicadores_válidos.items()}

            freqs = pd.Series({codigo: self.cuadros.loc[codigo, 'freq'] for codigo in indicadores_válidos.values()})
            freqs = freqs.astype('category').cat.set_categories(['A', '6M', 'Q', 'M', 'W', 'D'], ordered=True)

            if len(freqs)>1:  # es necesario convertir frecuencias
                freq = freq if freq else freqs.min()
                if callable(func):
                    func = {codigo: func for codigo in indicadores_válidos.values()}

                for nombre, codigo in indicadores_válidos.items():
                    if freqs[codigo] != freq:
                        datos[nombre] = datos[nombre].resample(freq).apply(func[codigo])

            results = pd.concat(datos.values(), keys=datos.keys(), axis=1)

            return results


    def __call__(self, *args, **kwargs):
        return self.datos(*args, **kwargs)

    def __buscar_frase__(self, frase):
        CAMPOS = ['title', 'subtitle']
        return pd.DataFrame([self.cuadros[campo].str.contains(frase, case=False) for campo in CAMPOS]).any()

    def buscar(self, todos=None, *, frase=None, algunos=None, frecuencia=None):
        """buscar códigos de indicadores según su descripción

        Parameters
        ----------
        frase, todos, algunos : str
            texto que debe aparecer en la descripción del indicador. Sólo una de estos tres parámetros debe utilizarse
            a la vez. 'frase' busca una coincidencia exacta, 'todos' que todas las palabras aparezcan (en cualquier
            orden), 'algunos' que al menos una de las palabras aparezca. La búsqueda no es sensible a mayúscula/minúscula.
            Si no se indica un parámetro [por ejemplo, PW.buscar('precios consumidor')], se asume que
            PW.buscar(todos='precio consumidor')
        frecuencia : str, optional. uno de ('Q', 'A', 'M', 'D')
            mostrar solo indicadores que tengan la frecuencia indicada.

        Returns
        -------
        pd.DataFrame

        Examples
        --------

        Para buscar un indicador que tenga todas las palabras "Índice", "precios", "consumidor" (en cualquier orden)

        >>> from bccr import PW
        >>> PW.buscar(todos="Índice precios consumidor")

        Para buscar un indicador que tenga la frase exacta "Índice de Precios al Consumidor"

        >>> PW.buscar(frase="Índice de Precios al Consumidor")

        Para buscar un indicador que tenga al menos una de las palabras "exportaciones" e "importaciones"

        >>> PW.buscar(algunos="exportaciones importaciones")

        Para buscar los términos "precios transables", y filtrar que muestre solo resultados con medida "Variación interanual"

        >>> PW.buscar('precios transables', Medida='Variación interanual')

        Para mostrar un breve mensaje de ayuda

        >>> PW.buscar()


        """


        CAMPOS = ['title', 'subtitle', 'freq']

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
                buscar(frase="descripción contiene esta frase literalmente")
                buscar(todos="descripción contiene todos estos términos en cualquir orden")
                buscar(algunos="descripción contiene alguno de estos términos")
                buscar()  # muestra este mensaje de ayuda
            """
            print(ayuda)
            return


        if frecuencia:
            freq = self.cuadros['freq'] == frecuencia[0].upper()
            return self.cuadros[temp & freq][CAMPOS]
        else:
            return self.cuadros[temp][CAMPOS]

    def __str__(self):
        return FRASE_AYUDA

    def __repr__(self):
        return self.__str__()


PW = PaginaWeb(pd.read_pickle(PICKLE_FILE))