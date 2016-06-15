import os
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup

from .download import api


CHARTFREQUENCIES = {
    'MonthYear': 'Monthly',
    'YearMonth': 'Monthly',
    'IndicatorYear': 'Annual',
    'IndicatorQuarter': 'Quarterly',
    'IndicatorMonth': 'Monthly',
    'QuarterIndicator': 'Quarterly',
    'MonthIndicator': 'Monthly',
    'DayYear': 'Daily',
    'NOT-SUPPORTED-YET': 'unknown'
}



def fastTitle(chart, quiet=True):
    """
        Read title of a single chart. Optimized for speed: try to download as little data as possible, if it fails then
        download using default dates
    Parameters
    ----------
    chart   : chart number (integer)

    Returns
    -------
            A pandas series with two elements (title and subtitle)
    """

    if not quiet:
        print(api(chart, excel=False))

    try:
        rawdata = pd.read_html(api(chart, 2015, 2015), thousands="")[0]
    except:
        rawdata = pd.read_html(api(chart), thousands="")[0]

    df = pd.DataFrame(index=[chart])
    df['title'], df['subtitle'], subts2 = rawdata.iloc[:3, 0]
    if not pd.isnull(subts2):
        df['subtitle'] += ' --- %s' % subts2

    return df


def readTitle(series, quiet=True):
    """
        Reads the title and subtitle of indicated series

    Parameters
    ----------
    series  : An iterable of integers, indicating chart numbers

    Returns
    -------
        A pandas dataframe, indexed by chart numbers

    """
    seriesSet = [series] if isinstance(series, int) else set(series)
    return pd.concat([fastTitle(v, quiet) for v in seriesSet])







def findAllCharts():
    baseURL = 'http://www.bccr.fi.cr/indicadores_economicos_/'

    pages = [
        'Encuestas_economicas',
        'Indices_Precios',
        'finanzas_publicas',
        'Mercados_negociacion',
        'Monetario_financiero',
        'Produccion_empleo',
        'Sector_Externo',
        'Tasas_interes',
        'Tipos_cambio']

    urls = {page: baseURL + page + '.html' for page in pages}


    pagesCharts = []
    for sector, url in urls.items():

        chartsList = list()

        access_page = requests.get(url).content
        soup = BeautifulSoup(access_page, 'lxml')
        url_list_of_indicators = soup.findAll('iframe')[0]['src']

        sector_page = requests.get(url_list_of_indicators).content
        soup = BeautifulSoup(sector_page, 'lxml')

        print('\n\nsector = ', sector)

        for kk in soup.find_all('a'):
            link = kk['href']
            if 'CodCuadro=' in link:
                chartsList.append(int(link.split('CodCuadro=')[1]))

        titlestable = readTitle(chartsList, False)
        titlestable['sector'] = sector
        print(titlestable)
        pagesCharts.append(titlestable)

    data = pd.concat(pagesCharts, axis=0)
    data['sector'] = pd.Categorical(data['sector'])

    '''SAVE THE DATA'''
    oldDir = os.getcwd()
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    pd.to_pickle(data, './data/asReadFromBCCR.pkl')
    os.chdir(oldDir)









def search(expression, match_all=True):
    """
        Find indicators by (partial) name match
    Parameters
    ----------
    expression  : A string to search in chart titles (case insensitive), terms separated by spaces
    match_all   : match all terms if True, match any term if False

    Returns
    -------
        A pandas dataframe with all charts whose titles contain a given string (case insensitive)

    Examples
    --------

        >>> search('producto')
        >>> search('tasa')
        >>> search('precio consumidor')
        >>> search('exportaciones importaciones')
        >>> search('exportaciones importaciones', False)
    """
    indicators = loadIndicators()

    tt = [indicators['title'].apply(lambda x: bool(re.search(name, x, re.IGNORECASE))) for name in expression.split()]
    tt = pd.concat(tt, axis=1)
    tt = tt.all(1) if match_all else tt.any(1)
    results = indicators.loc[tt, ['title', 'subtitle', 'chartFormat']]


    results['frequency'] = results['chartFormat'].apply(lambda x: CHARTFREQUENCIES[x].lower())

    return results[['title', 'subtitle', 'frequency']]


def loadIndicators():
    oldDir = os.getcwd()
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    indicators = pd.read_pickle('data/indicators.pkl')
    os.chdir(oldDir)
    return indicators


def dropDuplicateIndices(df):
    df.reset_index(inplace=True)
    df.drop_duplicates(subset='index', inplace=True)
    df.set_index('index', inplace=True)
    return df



def updateIndicators():
    oldDir = os.getcwd()
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    ''' OPEN DATABASES, DELETE DUPLICATES'''
    webData = dropDuplicateIndices(pd.read_pickle('./data/asReadFromBCCR.pkl'))
    chartData = dropDuplicateIndices(pd.read_excel('./data/allChartFormats.xlsx'))
    indicators = pd.concat([webData, chartData], axis=1)
    indicators['chartFormat'] = pd.Categorical(indicators['chartFormat'])
    indicators.index.names = ['chart']
    pd.to_pickle(indicators, './data/indicators.pkl')
    os.chdir(oldDir)
    return indicators
