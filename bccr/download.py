"""
This module contains functions to download data from Banco Central de Costa Rica.  Data is returned as tidy
pandas DataFrames, indexed as time series.


Randall Romero-Aguilar
May 2016
"""

import numpy as np
import pandas as pd
import webbrowser
import time
import re
import os


from .utils import *


pd.set_option('display.width', 500)
pd.set_option('display.max_colwidth', 120)


BCCR_URL = "http://indicadoreseconomicos.bccr.fi.cr/indicadoreseconomicos/"


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
    bccr_web = BCCR_URL + "Cuadros/frmVerCatCuadro.aspx?"
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
        A pandas DataFrame with data in the same format as in BCCR website.

    Examples
    --------
        1. Download data on money supply (M1) for 2011 to 2015

        >>> downloadChart(125, 2011, 2015)

        2. Same as before, but without printing download (name of series, url, retrieve date-time)

        >>> downloadChart(138, 2011, 2015, quiet=True)
    """
    rawdata = pd.read_html(api(chart, first, last), thousands="")[0]
    rawdata.columns = ['V%s' % k for k in range(rawdata.shape[1])]

    if not quiet:
        info = 'Downloading chart %s:' % chart
        for txt in rawdata['V0'][:2]:
            info += ('\n\t' + txt) if txt else ''
        info += '\n\tRetrieved %s from:' % time.strftime("%c")
        info += '\n\t\t' + api(chart, first, last, excel=False) + '\n'
        print(info)

    return rawdata

def readYearMonth(series, first=None, last=None, freq=None, func=None, quiet=True):
    """
        Reads BCCR charts where each row represents a year and each column represents a month.

    Parameters
    ----------
    series  : Charts to be downloaded, either an integer or a {int: str} dictionary.
    first   : The first year to download (integer, default=None).
    last    : The last year to download (integer, default=None)
    freq    : Data frequency (string, default=None).
    func    : How to summarize data in lower frequency (function, default=np.mean)
    quiet   : Print download info if False, nothing if True

    Returns
    -------
        Requested data, either as a pandas series (if series is int) or dataframe (if series is dict)

    Examples
    --------
        1. Download data on money supply

        >>> readYearMonth(125)

        2. Download data on money supply (M1) and current account deposits on colones (DCCMN) since 1999

        >>> readYearMonth({125: 'M1', 138: 'DCCMN'}, first=1999)  # data since 1999

        3. Same as before, but returning quarterly data (average of monthly observations)

        >>> readYearMonth({125: 'M1', 138: 'DCCMN'}, freq='Q')  # quarterly data (average of months)

        Once downloaded, the resulting pandas dataframe can be used for plots. The first plot combines all series in a
        single plot, the latter displays a subplot for each series.

        >>> data = readYearMonth({125: 'M1', 138: 'DCCMN'})
        >>> data.plot()
        >>> data.plot(subplots=True)
    """
    series, funcs = parseSeriesFreqInputs(series, func)

    rawdataList = []
    for chartNumber, varName in series.items():
        rawdata = downloadChart(chartNumber, first, last, quiet)
        varName = varName if varName else rawdata['V0'][0]
        h = findFirstElement('Enero', rawdata['V1'])
        rawdata.drop(rawdata.index[:h + 1], inplace=True)
        year0 = rawdata.iat[0, 0]
        del rawdata['V0']
        rawdata = tidy(rawdata.stack(dropna=False),
                       timeindex=pd.date_range(year0 + '/01', periods=rawdata.size, freq='M'),
                       freq=freq, func=funcs[chartNumber],
                       colnames= varName)
        rawdataList.append(rawdata)

    data = pd.concat(rawdataList, axis=1)
    return data


def readMonthYear(series, first=None, last=None, freq=None, func=None, quiet=True):
    """
        Reads BCCR charts where each row represents a month and each column represents a year.

    Parameters
    ----------
    series  : Charts to be downloaded, either an integer or a {int: str} dictionary.
    first   : The first year to download (integer, default=None).
    last    : The last year to download (integer, default=None)
    freq    : Data frequency (string, default=None).
    func    : How to summarize data in lower frequency (function, default=np.mean)
    quiet   : Print download info if False, nothing if True

    Returns
    -------
        Requested data, either as a pandas series (if series is int) or dataframe (if series is dict)

    Examples
    --------
        1. Download the consumer price index

        >>> readYearMonth(9)

        2. Download the CPI, and its tradable and non-tradable components, since 1999.

        >>> indices = {9: 'IPC', 289: 'IPC No transable', 290: 'IPC transable'}
        >>> readYearMonth(indices, first=1999)

        3. Same as before, but returning quarterly data by taking the average of monthly data.

        >>> data = readYearMonth(indices, freq='Q')

        Once downloaded, the resulting pandas dataframe can be used for plots. The first line combines all series in a
        single plot, the latter displays a subplot for each series.

        >>> data.plot(subplots=True)
    """
    series, funcs = parseSeriesFreqInputs(series, func)

    rawdataList = []
    for chartNumber, varName in series.items():
        rawdata = downloadChart(chartNumber, first, last, quiet)
        varName = varName if varName else rawdata['V0'][0]
        h = findFirstElement('Enero', rawdata['V0'])

        if 'Total' in str(rawdata.iloc[h-1, 0]):
            year0 = rawdata.iat[h-2, 1]
        else:
            year0 = rawdata.iat[h - 1, 1]
        rawdata.drop(rawdata.index[:h],inplace=True)
        del rawdata['V0']
        rawdata = tidy(rawdata.transpose().stack(dropna=False),
                       timeindex=pd.date_range(year0 + '/01', periods=rawdata.size, freq='M'),
                       freq=freq, func=funcs[chartNumber],
                       colnames= varName)
        rawdataList.append(rawdata)

    data = pd.concat(rawdataList, axis=1)
    return data


def readIndicatorYear(series, first=None, last=None, freq=None, func=None, quiet=True):
    """
        Reads BCCR charts where each row represents an indicator and each column represents a year.

    Parameters
    ----------
    series  : Charts to be downloaded, either an integer or a {int: str} dictionary.
    first   : The first year to download (integer, default=None).
    last    : The last year to download (integer, default=None)
    freq    : Data frequency (string, default=None).
    func    : How to summarize data in lower frequency (function, default=np.mean)
    quiet   : Print download info if False, nothing if True

    Returns
    -------
        Requested data as a pandas dataframe

    Examples
    --------
        1. Download data on FDI in Costa Rica, by country of origin

        >>> readIndicatorYear(2185)

        2. Download data on national accounts, constant prices

        >>> readIndicatorYear(189)

        3. Download data on national accounts, constant and current prices. Use *Real_* and *Nominal_* to tell them apart.

        >>> readIndicatorYear({189: 'Real_', 230: 'Nominal_'})
    """

    series, funcs = parseSeriesFreqInputs(series, func)

    rawdataList = []
    for chartNumber, varName in series.items():
        rawdata = downloadChart(chartNumber, first, last, quiet)
        h = findFirstElement('^[12]', rawdata['V1'])
        year0 = rawdata.iat[h, 1]
        rawdata.drop(rawdata.index[:h+1], inplace=True)
        indicators = rawdata['V0']
        del rawdata['V0']
        rawdata = rawdata.transpose()
        rawdata = tidy(rawdata,
                       timeindex=pd.date_range(year0 + '/12', periods=rawdata.shape[0], freq='A'),
                       freq=freq, func=funcs[chartNumber],
                       colnames= [varName + v for v in indicators])
        rawdataList.append(rawdata)

    data = pd.concat(rawdataList, axis=1)
    return data


def readIndicatorQuarter(series, first=None, last=None, freq=None, func=None, quiet=True):
    """
        Reads BCCR charts where each row represents an indicator and each column represents a quarter.

    Parameters
    ----------
    series  : Charts to be downloaded, either an integer or a {int: str} dictionary.
    first   : The first year to download (integer, default=None).
    last    : The last year to download (integer, default=None)
    freq    : Data frequency (string, default=None).
    func    : How to summarize data in lower frequency (function, default=np.mean)
    quiet   : Print download info if False, nothing if True

    Returns
    -------
        Requested data as a pandas dataframe

    Examples
    --------
        1. Download data on number of workers by economic activity

        >>> readIndicatorQuarter(1912)

        2. Download quarterly data on national accounts, constant prices, by industry

        >>> readIndicatorQuarter(64)

        3. Download quarterly data on national accounts, constant and current prices.
        Use *Real_* and *Nominal_* to tell them apart.

        >>> readIndicatorQuarter({68: 'Real_', 70: 'Nominal_'})
    """

    series, funcs = parseSeriesFreqInputs(series, func)

    rawdataList = []
    for chartNumber, varName in series.items():
        rawdata = downloadChart(chartNumber, first, last, quiet)
        h = findFirstElement('^trim', rawdata['V1'])
        quarter0 = parseQuarterYear(rawdata.iloc[h, 1])
        rawdata.drop(rawdata.index[:h+1], inplace=True)
        indicators = rawdata['V0']
        del rawdata['V0']
        rawdata = rawdata.transpose()
        rawdata = tidy(rawdata,
                       timeindex=pd.date_range(quarter0, periods=rawdata.shape[0], freq='Q'),
                       freq=freq, func=funcs[chartNumber],
                       colnames= [varName + v for v in indicators])
        rawdataList.append(rawdata)

    data = pd.concat(rawdataList, axis=1)
    return data



def readQuarterIndicator(series, first=None, last=None, freq=None, func=None, quiet=True):
    """
        Reads BCCR charts where each row represents a quarter and each column represents an indicator.

    Parameters
    ----------
    series  : Charts to be downloaded, either an integer or a {int: str} dictionary.
    first   : The first year to download (integer, default=None).
    last    : The last year to download (integer, default=None)
    freq    : Data frequency (string, default=None).
    func    : How to summarize data in lower frequency (function, default=np.mean)
    quiet   : Print download info if False, nothing if True

    Returns
    -------
        Requested data as a pandas dataframe

    Examples
    --------
        1. Download data on number of workers by economic activity

        >>> readIndicatorQuarter(1912)  # FIXME UPDATE DOCUMENTATION

        2. Download quarterly data on national accounts, constant prices, by industry

        >>> readIndicatorQuarter(64)

        3. Download quarterly data on national accounts, constant and current prices.
        Use *Real_* and *Nominal_* to tell them apart.

        >>> readIndicatorQuarter({68: 'Real_', 70: 'Nominal_'})
    """

    series, funcs = parseSeriesFreqInputs(series, func)

    rawdataList = []
    for chartNumber, varName in series.items():
        rawdata = downloadChart(chartNumber, first, last, quiet)
        h = findFirstElement('^trim', rawdata['V0'])
        quarter0 = parseQuarterYear(rawdata.iloc[h, 0])

        indicators = rawdata.iloc[h-1, 1:]
        rawdata.drop(rawdata.index[:h], inplace=True)
        del rawdata['V0']
        rawdata = tidy(rawdata,
                       timeindex=pd.date_range(quarter0, periods=rawdata.shape[0], freq='Q'),
                       freq=freq, func=funcs[chartNumber],
                       colnames= [varName + v for v in indicators])
        rawdataList.append(rawdata)

    data = pd.concat(rawdataList, axis=1)
    return data




def readDayYear(series, first=None, last=None, freq=None, func=None, quiet=False):
    """
        Reads BCCR charts where each row represents a day and each column represents a year.

    Parameters
    ----------
    series  : Charts to be downloaded, either an integer or a {int: str} dictionary.
    first   : The first year to download (integer, default=None).
    last    : The last year to download (integer, default=None)
    freq    : Data frequency (string, default=None).
    func    : How to summarize data in lower frequency (function, default=np.mean)
    quiet   : Print download info if False, nothing if True

    Returns
    -------
        Requested data, either as a pandas series (if series is int) or dataframe (if series is dict)

    Examples
    --------
        1. Download the Tasa basica (interest rate)

        >>> readDayYear(17)

        2. Download the Tasa basica (chart 17) and the exchange rate (chart 367), since 2000. Assign short names to series.

        >>> series = {17: 'tbp', 367: 'xr'}
        >>> readDayYear(series, first=2000)

        3. Same series as before, but returning quarterly data by taking the average of daily data.

        >>> data = readDayYear(series, freq='Q')

        Once downloaded, the resulting pandas dataframe can be used for plots. Here, we plot data from September 2006 to
        December 2009, showing each time series in a subplot.

        >>> data.plot()
        >>> data['2006-9':'2009-12'].plot(subplots=True)
    """
    series, funcs = parseSeriesFreqInputs(series, func)

    rawdataList = []
    for chartNumber, varName in series.items():
        rawdata = downloadChart(chartNumber, first, last, quiet)
        varName = varName if varName else rawdata['V0'][0]
        h = findFirstElement('1 Ene', rawdata['V0'])
        year0 = rawdata.iat[h - 1, 1]
        rawdata.drop(rawdata.index[:h],inplace=True)
        del rawdata['V0']

        # deal with leap years
        years = np.arange(int(year0), int(year0) + rawdata.shape[1])
        nonleap = ~ is_leap_year(years)
        rawdata.iloc[59, nonleap] = 'DELETE ME'   # row 59 = Feb 29 (counting from zero-base)
        rawdata = rawdata.transpose().stack(dropna=False)
        rawdata = rawdata[rawdata != 'DELETE ME']

        rawdata = tidy(rawdata,
                       timeindex=pd.date_range(year0 + '/01', periods=rawdata.size, freq='D'),
                       freq=freq, func=funcs[chartNumber],
                       colnames= varName)
        rawdataList.append(rawdata)

    data = pd.concat(rawdataList, axis=1)
    return data


def comprar(ingreso, precio):
    pass




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
    if isinstance(series, int):
        return fastTitle(series)

    series = set(series)  # to eliminate duplicates

    rawdata = pd.DataFrame([fastTitle(v) for v in series])
    rawdata.index = series
    rawdata.columns = ['title', 'subtitle']
    return rawdata


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
        txt = downloadChart(chart, 2015, 2015, quiet=True)['V0'][:2]
    except:
        txt = downloadChart(chart, quiet=True)['V0'][:2]
    return txt


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

    return indicators.loc[tt, ['title', 'subtitle', 'function']]  #fixme function should later be removed



READMETHODS = {
    'readMonthYear': readMonthYear,
    'readYearMonth': readYearMonth,
    'readIndicatorYear': readIndicatorYear,
    'readIndicatorQuarter': readIndicatorQuarter,
    'readQuarterIndicator': readQuarterIndicator,
    'readDayYear': readDayYear
}







def read(series, first=None, last=None, freq=None, func=None, quiet=True):
    """
        Reads BCCR charts.
        * This function allows downloading of charts of different formats in a single call.
        * If no frequency parameter is specified, then it will return the lowest frequency
        found in the data sets.
         * If no func parameter is specified, then higher-to lower conversion is done by taking the
         average of the data. By using a dictionary, user can specify different conversion methods for
         different charts.

    Parameters
    ----------
    series  : Charts to be downloaded, either an integer or a {int: str} dictionary.
    first   : The first year to download (integer, default=None).
    last    : The last year to download (integer, default=None)
    freq    : Data frequency (string, default=None).
    func    : How to summarize data in lower frequency (function, default=np.mean)
    quiet   : Print download info if False, nothing if True

    Returns
    -------
        Requested data, either as a pandas series (if series is int) or dataframe (if series is dict)

    """

    series, funcs = parseSeriesFreqInputs(series, func)
    indicators = loadIndicators().loc[list(series.keys()), ['title', 'function']]

    if freq is None:
        original_frequencies = set([CHARTFREQUENCIES[k] for k in indicators['function']])
        if len(original_frequencies) > 1:
            freq = lowestFrequency(original_frequencies)
            print('\nDownloading data with frequencies : %s !!!' % original_frequencies)
            print('Returning frequency: %s\n' % freq)



    rawdataList = []
    for method, subseries in indicators.groupby('function'):
        minidata = READMETHODS[method](subseries['title'], first, last, freq, funcs, quiet)
        rawdataList.append(minidata)

    data = pd.concat(rawdataList, axis=1)
    return data
