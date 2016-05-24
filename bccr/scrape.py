from bs4 import BeautifulSoup
import requests
import webbrowser
from .download import readTitle
import pandas as pd


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