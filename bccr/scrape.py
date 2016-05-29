import os
import re

from bs4 import BeautifulSoup
import requests
import webbrowser
import pandas as pd

from .download import downloadChart


CHARTFREQUENCIES = {
    'readMonthYear': 'Monthly',
    'readYearMonth': 'Monthly',
    'readIndicatorYear': 'Annual',
    'readIndicatorQuarter': 'Quarterly',
    'readIndicatorMonth': 'Monthly',
    'readQuarterIndicator': 'Quarterly',
    'readDayYear': 'Daily',
    'NOT-SUPPORTED-YET': 'unknown'
}



def fastTitle(chart):
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
    try:
        data, title, subtitle = downloadChart(chart, 2015, 2015, quiet=True)
    except:
        data, title, subtitle = downloadChart(chart, quiet=True)
    df = pd.DataFrame(index=[chart])
    df['title'] = title
    df['subtitle'] = subtitle
    return df


def readTitle(series):
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
    return pd.concat([fastTitle(v) for v in seriesSet])







def findAllCharts():
    baseURL = 'http://www.bccr.fi.cr/indicadores_economicos_/'

    pages = ['Indices_Precios',
             'finanzas_publicas',
             'Mercados_negociacion',
             'Monetario_financiero',
             'Produccion_empleo',
             'Sector_Externo',
             'Tasas_interes',
             'Tipos_cambio']

    urls = {page: baseURL + page + '.html' for page in pages}


    pagesCharts = {}
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




        titlestable = readTitle(chartsList)
        titlestable['sector'] = sector
        print(titlestable)
        pagesCharts[sector] = titlestable

    data = pd.concat(pagesCharts, axis=0)
    data['sector'] = pd.Categorical(data['sector'])
    pd.to_pickle(data, 'datos.pkl')







def findIndicators(expression, match_all=True):
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

        >>> findIndicators('producto')
        >>> findIndicators('tasa')
        >>> findIndicators('precio consumidor')
        >>> findIndicators('exportaciones importaciones')
        >>> findIndicators('exportaciones importaciones', False)
    """
    indicators = loadIndicators()

    tt = [indicators['title'].apply(lambda x: bool(re.search(name, x, re.IGNORECASE))) for name in expression.split()]
    tt = pd.concat(tt, axis=1)
    tt = tt.all(1) if match_all else tt.any(1)
    results = indicators.loc[tt, ['title', 'subtitle', 'function']]



    results['frequency'] = results['function'].apply(lambda x: CHARTFREQUENCIES[x].lower())

    return results[['title', 'subtitle', 'frequency']]


def loadIndicators():
    oldDir = os.getcwd()
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    indicators = pd.read_pickle('data/indicators.pkl')
    os.chdir(oldDir)
    return indicators


