from dataclasses import dataclass
import pandas as pd
import numpy as np
import os
import time
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
    cuadros: pd.DataFrame = pd.read_pickle(PICKLE_FILE)

    def api(self, Cuadro, FechaInicio=None, FechaFinal=None, excel=True, abrir=False):
        """
            Builds a valid url to access data from the BCCR website

        Parameters
        ----------
        Cuadro  : A number identifying the BCCR's data table (integer).
        FechaInicio  : The FechaInicio year to download (integer, default=None).
        FechaFinal   : The FechaFinal year to download (integer, default=None)
        excel   : Whether to export query as Excel file (boolean, default=TRUE)
        abrir   : Whether to abrir the table in the computer's browser (boolean, default=FALSE)

        Returns
        -------
            A valid URL to download the data from indicated Cuadro (string).

        Examples
        --------
            1. Get the url to download the consumer price index (Cuadro 9), using default settings

            >>> self.api(9)
            http://indicadoreseconomicos.bccr.fi.cr/indicadoreseconomicos/Cuadros/frmVerCatCuadro.aspx?CodCuadro=9&Exportar=True&Excel=True

            2. Get the url to download the money supply (M1, Cuadro 125) since 2010

            >>> self.api(125, 2010)
            http://indicadoreseconomicos.bccr.fi.cr/indicadoreseconomicos/Cuadros/frmVerCatCuadro.aspx?CodCuadro=125&FecInicial=2010/01/01&Exportar=True&Excel=True

            3. Get the url to download the non-tradable CPI (Cuadro 289) between 2010 and 2015

            >>> self.api(289, 2010, 2015)
            http://indicadoreseconomicos.bccr.fi.cr/indicadoreseconomicos/Cuadros/frmVerCatCuadro.aspx?CodCuadro=289&FecInicial=2010/01/01&FecFinal=2015/12/31&Exportar=True&Excel=True

            4. Get url to download money supply between 2010 and 2015, but in HTML format (as opposed to the default Excel format)

            >>> self.api(125, 2010, 2015, excel=False)
            http://indicadoreseconomicos.bccr.fi.cr/indicadoreseconomicos/Cuadros/frmVerCatCuadro.aspx?CodCuadro=125&FecInicial=2010/01/01&FecFinal=2015/12/31

            5. Same as before, but using default dates. The abrir=True option opens your default browser with the selected data.

            >>> self.api(125, excel=False, abrir=True)  # opens link in browser
            http://indicadoreseconomicos.bccr.fi.cr/indicadoreseconomicos/Cuadros/frmVerCatCuadro.aspx?CodCuadro=125
        """
        bccr_web = "https://gee.bccr.fi.cr/indicadoreseconomicos/"

        bccr_web += "Cuadros/frmVerCatCuadro.aspx?"
        params = dict(CodCuadro=Cuadro)
        if FechaInicio:
            params['FecInicial'] = parse_date_parameter(FechaInicio, inicio=True)
        if FechaFinal:
            params['FecFinal'] = parse_date_parameter(FechaFinal, inicio=False)
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
        Cuadro   : Un número que identifica un cuadro del BCCR (int).

        Returns
        -------
            None

        Examples
        --------
            1. Abrir cuadro 125

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

    def datos(self, *Cuadros, FechaInicio=None, FechaFinal=None, func=np.sum, freq=None, info=False):
        """
        Descargar datos del Servicio Web del BCCR:
        Construye una consulta por método GET a partir de los parámetros proporcionados, para cada uno de los
        Indicadores solicitados. Descarga los datos, los transforma en una tabla de datos de Pandas.
        Si hay indicadores de distintas frecuecias, los transforma a la misma frecuencia según el método indicado.

        Parameters
        ----------
        Cuadros:  lista de cuadros a consultar (str o int o iterable)
        FechaInicio: fecha de primera observación, formato dd/mm/yyyy. (str, opcional, '01/01/1900')
        FechaFinal: fecha de primera observación, formato dd/mm/yyyy. (str, opcional, fecha de hoy)
        SubNiveles: si descargar subniveles del Indicador (bool, opcional, False)

        Returns
        -------
        Datos en formato pandas.DataFrame
        """
        # desempacar Indicadores si viene en una colección
        if len(Cuadros)==1 and hasattr(Cuadros[0], '__iter__') and type(Cuadros) is not str:
            Cuadros = Cuadros[0]

        # determinar si insumo es diccionario
        if isinstance(Cuadros, dict):
            renombrar = True
            variables = {str(k): v for k, v in Cuadros.items()}  # convertir llaves a str, para renombrar
        else:
            renombrar = False

        # Convertir numeros de cuadros a enteros
        Cuadros = [int(x) for x in Cuadros]

        #__parse__(self, chart, first=None, last=None, freq=None, func=None, quiet=True):
        datos = {codigo: self.__parse__(codigo, first=FechaInicio, last=FechaFinal, freq=freq, func=func, quiet=not info) for codigo in Cuadros}

        freqs = pd.Series({codigo: self.cuadros.loc[codigo, 'freq'] for codigo in Cuadros})
        freqs = freqs.astype('category').cat.set_categories(['A', '6M', 'Q', 'M', 'W', 'D'], ordered=True)

        if len(freqs)>1:  # es necesario convertir frecuencias
            freq = freq if freq else freqs.min()
            if callable(func):
                func = {codigo: func for codigo in Cuadros}

            for codigo in Cuadros:
                if freqs[codigo] != freq:
                    datos[codigo] = datos[codigo].resample(freq).apply(func[codigo])

        results = pd.concat(datos.values(), axis=1)
        if renombrar:
            results.rename(columns=variables, inplace=True)

        return results


    def __call__(self, *args, **kwargs):
        return self.datos(*args, **kwargs)

    def __buscar_frase__(self, frase):
        CAMPOS = ['title', 'subtitle']
        return pd.DataFrame([self.cuadros[campo].str.contains(frase, case=False) for campo in CAMPOS]).any()

    def buscar(self, *, frase=None, todos=None, algunos=None, frecuencia=None):
        """
        Buscar palabras en la descripción de las variables en el catálogo.
        Parameters
        ----------
        frase
        todos
        algunos
        frecuencia

        Returns
        -------

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


PW = PaginaWeb()