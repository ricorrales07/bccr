"""
This module contains functions to download data from Banco Central de Costa Rica.  Data is returned as tidy
pandas DataFrames, indexed as time series.


Randall Romero-Aguilar
May 2016
"""

import time
import webbrowser
import pandas as pd

from .utils import findColumnTitles, fixCommas

pd.set_option('display.width', 500)
pd.set_option('display.max_colwidth', 120)


def api(chart, first=None, last=None, excel=True, open=False):
    """
        Builds a valid url to access data from the BCCR website

    Parameters
    ----------
    chart   : A number identifying the BCCR's data table (integer).
    first   : The first year to download (integer, default=None).
    last    : The last year to download (integer, default=None)
    excel   : Whether to export query as Excel file (boolean, default=TRUE)
    open    : Whether to open the table in the computer's browser (boolean, default=FALSE)

    Returns
    -------
        A valid URL to download the data from indicated chart (string).

    Examples
    --------
        1. Get the url to download the consumer price index (chart 9), using default settings

        >>> api(9)
        http://indicadoreseconomicos.bccr.fi.cr/indicadoreseconomicos/Cuadros/frmVerCatCuadro.aspx?CodCuadro=9&Exportar=True&Excel=True

        2. Get the url to download the money supply (M1, chart 125) since 2010

        >>> api(125, 2010)
        http://indicadoreseconomicos.bccr.fi.cr/indicadoreseconomicos/Cuadros/frmVerCatCuadro.aspx?CodCuadro=125&FecInicial=2010/01/01&Exportar=True&Excel=True

        3. Get the url to download the non-tradable CPI (chart 289) between 2010 and 2015

        >>> api(289, 2010, 2015)
        http://indicadoreseconomicos.bccr.fi.cr/indicadoreseconomicos/Cuadros/frmVerCatCuadro.aspx?CodCuadro=289&FecInicial=2010/01/01&FecFinal=2015/12/31&Exportar=True&Excel=True

        4. Get url to download money supply between 2010 and 2015, but in HTML format (as opposed to the default Excel format)

        >>> api(125, 2010, 2015, excel=False)
        http://indicadoreseconomicos.bccr.fi.cr/indicadoreseconomicos/Cuadros/frmVerCatCuadro.aspx?CodCuadro=125&FecInicial=2010/01/01&FecFinal=2015/12/31

        5. Same as before, but using default dates. The open=True option opens your default browser with the selected data.

        >>> api(125, excel=False, open=True)  # opens link in browser
        http://indicadoreseconomicos.bccr.fi.cr/indicadoreseconomicos/Cuadros/frmVerCatCuadro.aspx?CodCuadro=125
    """
    bccr_web = "http://indicadoreseconomicos.bccr.fi.cr/indicadoreseconomicos/"
    bccr_web += "Cuadros/frmVerCatCuadro.aspx?"
    bccr_web += "CodCuadro=%s" % chart
    bccr_web += "&FecInicial=%s/01/01" % first if first else ""
    bccr_web += "&FecFinal=%s/12/31" % last if last else ""
    bccr_web += "&Exportar=True&Excel=True" if excel else ""

    if open:
        webbrowser.open(bccr_web)

    return bccr_web


def downloadChart(chart, first=None, last=None, quiet=False):
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

        >>> downloadChart(125, 2011, 2015)

        2. Same as before, but without printing download info(name of series, url, retrieved date-time)

        >>> downloadChart(138, 2011, 2015, quiet=True)
    """
    rawdata = pd.read_html(api(chart, first, last), thousands="")[0]
    title, subtitle, subts2 = rawdata.iloc[:3, 0]
    if pd.notnull(subts2):
        subtitle += ' --- %s' % subts2

    rawdata.set_index(0, inplace=True)
    h = findColumnTitles(rawdata)
    rawdata.columns = rawdata.iloc[h]
    rawdata = rawdata.iloc[h+1:].applymap(fixCommas)

    if not quiet:
        info = 'Downloading chart %s:' % chart
        info += ('\n\t' + title) if title else ''
        info += ('\n\t' + subtitle) if subtitle else ''
        info += '\n\tRetrieved %s from:' % time.strftime("%c")
        info += '\n\t' + api(chart, first, last, excel=False) + '\n'
        print(info)

    rawdata._metadata = {'title': title, 'subtitle': subtitle}
    return rawdata


def web(chart):
    """
        Opens the specified chart in the BCCR website, using the default Internet browser.

    Parameters
    ----------
    series   : A number identifying the BCCR's data table (integer).

    Returns
    -------
        None

    Examples
    --------
        1. Open chart 125

        >>> web(125)
    """

    api(chart, first=None, last=None, excel=False, open=True)
    return