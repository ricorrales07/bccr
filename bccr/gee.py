
import pandas as pd
import numpy as np
from anytree import Node, RenderTree
import requests
import os
from dataclasses import dataclass
from datetime import datetime
from bs4 import BeautifulSoup
from numpy import nan
import re
from .utils import parse_date_parameter

BCCR_FOLDER = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(BCCR_FOLDER, 'data')
PICKLE_FILE = os.path.join(DATA_FOLDER, 'indicadores.pkl')
EXCEL_FILE =  os.path.join(DATA_FOLDER, 'Indicadores.xlsx')

FRASE_AYUDA = """
CLASE ServicioWeb

Esta clase permite buscar y descargar datos de indicadores del servicio web del Banco Central de Costa Rica.
Suponiendo que el objeto de clase ServicioWeb se llama "consulta":
    * para buscar indicadores, utilice 
        consulta.buscar()
    * para saber más detalles del indicador 8 (por ejemplo)
        consulta.quien(8)
    * para buscar las subcuentas de un indicador, digamos el 784
        consulta.subcuentas(784)      
    * para descargar datos de indicadors 4, 7 y 231 (por ejemplo), hay varias formas de hacerlo 
        consulta(4, 7, 231)   # pasando los códigos directamente
        consulta([4, 7, 231]) # pasando los códigos en una lista
        consulta({'4':'indicA', '7':'indicB', '231':'indicC'} # pasando los códigos en un diccionario, en 
            cuyo caso los indicadores son renombrados como 'indicA', 'indicB' y 'indicC', respectivamente.        
"""




#TODO: Arreglar problema de fechas duplicadas! ejemplo monex 3223 en 2010
#TODO: Arreglar missing values mal codificados! ejemplo monex 3223 aparecen 0s en vez de missing values


@dataclass
class ServicioWeb:
    nombre: str = 'Paquete BCCR Python'
    correo: str = 'paquete.bccr.python@outlook.com'
    token: str = '5CMRCBTHMT'
    indicadores: pd.DataFrame = pd.read_pickle(PICKLE_FILE)

    def __usuario__(self):
        """
        Credenciales de usuario.
        Para uso interno de la clase, en la función descargar

        Returns
        -------
        Un diccionario: (nombre, correo electrónico, token)
        """

        return dict(Nombre=self.nombre, CorreoElectronico=self.correo, Token=self.token)

    def __observacion__(self, obs):
        """
        Observación: extrae código de variable, fecha y valor de una observación.
        Para uso interno de la clase, en la función descargar.

        Parameters
        ----------
        obs: Una observación del archivo XML descargado de BCCR, resultado de BeautifulSoup

        Returns
        -------
        Una tupla con:
            --codigo: el código del indicador (str)
            --fecha: la fecha de la observación (str)
            --valor: el valor de la observación (float)

        """

        CODIGO = obs.find('COD_INDICADORINTERNO').text
        FECHA = obs.find('DES_FECHA').text[:10]
        VALOR = float(obs.find('NUM_VALOR').text) if obs.find('NUM_VALOR') else nan
        return CODIGO, FECHA, VALOR

    def __descargar__(self, Indicador, FechaInicio=None, FechaFinal=None, SubNiveles=False, indexar=True):
        """
        Descargar datos del Servicio Web del BCCR:
        Construye una consulta por método GET a partir de los parámetros proporcionados. Descarga los datos
        y los transforma en una tabla de datos de Pandas.
        Para uso interno de la clase, para la función datos.

        Parameters
        ----------
        Indicador:  indicador a consultar (str o int)
        FechaInicio: fecha de primera observación, formato dd/mm/yyyy. (str, opcional, '01/01/1900')
        FechaFinal: fecha de primera observación, formato dd/mm/yyyy. (str, opcional, fecha de hoy)
        SubNiveles: si descargar subniveles del Indicador (bool, opcional, False)

        Returns
        -------
        Datos en formato pandas.DataFrame
        """

        Indicador = str(Indicador)
        params = self.__usuario__()
        params['Indicador'] = Indicador
        params['FechaInicio'] = parse_date_parameter(FechaInicio) if FechaInicio else '01/01/1900'
        params['FechaFinal'] = parse_date_parameter(FechaFinal,inicio=False) if FechaFinal else datetime.now().strftime('%d/%m/%Y')
        params['SubNiveles'] = 'S' if SubNiveles else 'N'

        host = 'https://gee.bccr.fi.cr/Indicadores/Suscripciones/WS/wsindicadoreseconomicos.asmx/ObtenerIndicadoresEconomicos'
        resp = requests.get(host, params)

        if resp.status_code == 200: # datos recibidos exitosamente
            rawdata = resp.text
            soup = BeautifulSoup(rawdata, 'xml')
            observaciones = soup.find_all('INGC011_CAT_INDICADORECONOMIC')
            if observaciones:
                datos = [self.__observacion__(y) for y in observaciones]
                datos = pd.DataFrame(datos, columns=['variable', 'fecha','valor'])
                if indexar:
                    datos = datos.set_index(['variable', 'fecha']).unstack(level=0)['valor']
                    t0 = datos.index[0]
                    freq = self.indicadores.loc[Indicador,'freq']
                    T = datos.shape[0]
                    datos.index = pd.period_range(start=t0,freq=freq, periods=T)
                    return datos.dropna(how='all')
                else:
                    return datos

            print(f'\nNo se obtuvieron datos de indicador {Indicador}. Servidor respondio con mensaje ', resp.reason)
        else:
            print(f'\nNo se obtuvieron datos de indicador {Indicador}. Servidor respondio con mensaje ', resp.reason)


    def __buscar_frase__(self, frase):
        CAMPOS = ['DESCRIPCION', 'descripcion']
        return pd.DataFrame([self.indicadores[campo].str.contains(frase, case=False) for campo in CAMPOS]).any()

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
                buscar(frase="descripción contiene esta frase literalmente")
                buscar(todos="descripción contiene todos estos términos en cualquir orden")
                buscar(algunos="descripción contiene alguno de estos términos")
                buscar()  # muestra este mensaje de ayuda
            """
            print(ayuda)
            return

        if frecuencia:
            freq = self.indicadores['freq'] == frecuencia[0].upper()
            return self.indicadores[temp & freq][CAMPOS]
        else:
            return self.indicadores[temp][CAMPOS]


    def actualizar_catalogo(self):
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
        lista = str(node)[12:-1].split('/')
        for i, n in enumerate(lista):
            print('|' + '-' * (3 * (i + 1)) + ' ' + n)

    def quien(self, codigo):
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

    def subcuentas(self, codigo):
        cta = self.indicadores.loc[str(codigo), 'node']
        treestr = RenderTree(cta).by_attr()
        print(treestr)
        return re.findall('\[([0-9]+)\]', treestr)

    def datos(self, *Indicadores, FechaInicio=None, FechaFinal=None, SubNiveles=False, func=np.sum, freq=None):
        """
        Descargar datos del Servicio Web del BCCR:
        Construye una consulta por método GET a partir de los parámetros proporcionados, para cada uno de los
        Indicadores solicitados. Descarga los datos, los transforma en una tabla de datos de Pandas.
        Si hay indicadores de distintas frecuecias, los transforma a la misma frecuencia según el método indicado.

        Parameters
        ----------
        Indicadores:  lista de indicadores a consultar (str o int o iterable)
        FechaInicio: fecha de primera observación, formato dd/mm/yyyy. (str, opcional, '01/01/1900')
        FechaFinal: fecha de primera observación, formato dd/mm/yyyy. (str, opcional, fecha de hoy)
        SubNiveles: si descargar subniveles del Indicador (bool, opcional, False)

        Returns
        -------
        Datos en formato pandas.DataFrame
        """
        # desempacar Indicadores si viene en una colección
        if len(Indicadores)==1 and hasattr(Indicadores[0], '__iter__') and type(Indicadores) is not str:
            Indicadores = Indicadores[0]

        # determinar si insumo es diccionario
        if isinstance(Indicadores, dict):
            renombrar  = True
            variables = Indicadores.copy()
        else:
            renombrar = False

        # Convertir numeros de cuadros a textos
        Indicadores = [str(x) for x in Indicadores]

        datos = {codigo: self.__descargar__(codigo, FechaInicio, FechaFinal, SubNiveles) for codigo in Indicadores}

        freqs = pd.Series({codigo: self.indicadores.loc[codigo, 'freq'] for codigo in Indicadores})
        freqs = freqs.astype('category').cat.set_categories(['A', '6M', 'Q', 'M', 'W', 'D'], ordered=True)

        if len(freqs)>1:  # es necesario convertir frecuencias
            freq = freq if freq else freqs.min()
            if callable(func):
                func = {codigo: func for codigo in Indicadores}

            for codigo in Indicadores:
                if freqs[codigo] != freq:
                    datos[codigo] = datos[codigo].resample(freq).apply(func[codigo])

        salida = pd.concat(datos.values(), axis=1)
        return salida.rename(columns=variables) if renombrar else salida

    def __call__(self, *args, **kwargs):
        return self.datos(*args, **kwargs)

    def __str__(self):
        return FRASE_AYUDA

    def __repr__(self):
        return self.__str__()