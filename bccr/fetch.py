import numpy as np
import pandas as pd

from .download import downloadChart
from .scrape import loadIndicators, CHARTFREQUENCIES
from .utils import parseQuarterYear, parseMonthYear, is_leap_year, parseSeriesFreqInputs, lowestFrequency, parseDay

FIRST_OBSERVATION = {
    'YearMonth': lambda data: data.index[0] + '/01',
    'MonthYear': lambda data: data.columns[0] + '/01',
    'IndicatorYear': lambda data: data.columns[0] + '/12',
    'IndicatorQuarter': lambda data: parseQuarterYear(data.columns[0]),
    'QuarterIndicator': lambda data: parseQuarterYear(data.index[0]),
    'MonthIndicator': lambda data: parseMonthYear(data.index[0]),
    'IndicatorMonth': lambda data: parseMonthYear(data.columns[0]),
    'DayYear': lambda data: '%s/01/01' % data.columns[0],
    'DayIndicator': lambda data: parseDay(data.index[0])
}

def parse(chart, chartFormat, name=None, first=None, last=None, freq=None, func=None, quiet=True):
    #TODO: Add chartFormat='DayIndicator' to the possible options!!! Example chart=572

    data = downloadChart(chart, first, last, quiet)
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

    ''' RENAME TIME SERIES AND DROP MISSING VALUES '''
    if isinstance(data, pd.Series):
        data.name = name if name else title
        data.dropna(inplace=True)
    elif isinstance(data, pd.DataFrame):
        data.columns = [name + txt for txt in data.columns]
        data = data.dropna(0, 'all').dropna(1, 'all')
    else:
        raise ValueError('Unexpected data type: %s' % type(data))

    ''' RESAMPLE DATA '''
    if freq:
        func = func if func else np.mean
        data = data.resample(freq).apply(func)

    return data


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


    Examples
    --------
        1. Download data on money supply (chart 125)

        >>> read(125)

        2. Download data on money supply (chart 125) and current account deposits on colones chart (138) since 1999. Rename
        the series as 'M1' and 'DCCMN', respectively.

        >>> read({125: 'M1', 138: 'DCCMN'}, first=1999)

        3. Same as previous example, but returning quarterly data (average of monthly observations)

        >>> read({125: 'M1', 138: 'DCCMN'}, first=1999, freq='Q')

        4. Download the consumer price index (chart 9), tradable prices (290) and non-tradable prices (289)

        >>> read(9)

        2. Download the CPI, and its tradable and non-tradable components, since 1999.

        >>> indices = {9: 'IPC', 289: 'IPC No transable', 290: 'IPC transable'}
        >>> read(indices, first=1999)








        Once downloaded, the resulting pandas dataframe can be used for plots. The first plot combines all series in a
        single plot, the latter displays a subplot for each series.

        >>> data = read({125: 'M1', 138: 'DCCMN'})
        >>> data.plot()
        >>> data.plot(subplots=True)

    Examples
    --------
        1. Download the consumer price index

        >>> read(9)

        2. Download the CPI, and its tradable and non-tradable components, since 1999.

        >>> indices = {9: 'IPC', 289: 'IPC No transable', 290: 'IPC transable'}
        >>> read(indices, first=1999)

        3. Same as before, but returning quarterly data by taking the average of monthly data.



    Examples
    --------
        1. Download data on FDI in Costa Rica, by country of origin

        >>> readIndicatorYear(2185)

        2. Download data on national accounts, constant prices

        >>> readIndicatorYear(189)

        3. Download data on national accounts, constant and current prices. Use *Real_* and *Nominal_* to tell them apart.

        >>> readIndicatorYear({189: 'Real_', 230: 'Nominal_'})

    Examples
    --------
        1. Download data on number of workers by economic activity

        >>> readIndicatorQuarter(1912)

        2. Download quarterly data on national accounts, constant prices, by industry

        >>> readIndicatorQuarter(64)

        3. Download quarterly data on national accounts, constant and current prices.
        Use *Real_* and *Nominal_* to tell them apart.

        >>> readIndicatorQuarter({68: 'Real_', 70: 'Nominal_'})

    Examples
    --------
        1. Download data on number of workers by economic activity

        >>> readIndicatorQuarter(1912)  # FIXME UPDATE DOCUMENTATION

        2. Download quarterly data on national accounts, constant prices, by industry

        >>> readIndicatorQuarter(64)

        3. Download quarterly data on national accounts, constant and current prices.
        Use *Real_* and *Nominal_* to tell them apart.

        >>> readIndicatorQuarter({68: 'Real_', 70: 'Nominal_'})

    Examples
    --------
        1. Download data on number of workers by economic activity

        >>> readIndicatorQuarter(1912)  # FIXME UPDATE DOCUMENTATION

        2. Download quarterly data on national accounts, constant prices, by industry

        >>> readIndicatorQuarter(64)

        3. Download quarterly data on national accounts, constant and current prices.
        Use *Real_* and *Nominal_* to tell them apart.

        >>> readIndicatorQuarter({68: 'Real_', 70: 'Nominal_'})

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

    seriesDict, funcdict = parseSeriesFreqInputs(series, func)
    indicators = loadIndicators()['chartFormat'][list(seriesDict.keys())]

    if freq is None:
        original_frequencies = indicators.map(CHARTFREQUENCIES)
        if original_frequencies.unique().size > 1:
            freq = lowestFrequency(original_frequencies)
            print('\nDownloading data with frequencies : %s !!!' % original_frequencies.unique())
            print('Returning frequency: %s\n' % freq)

    return pd.concat(
        [parse(chart, indicators[chart], name, first, last, freq, funcdict[chart], quiet) for chart, name in seriesDict.items()],
        axis=1)