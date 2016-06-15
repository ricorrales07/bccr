import numpy as np
import pandas as pd

from .download import downloadChart
from .scrape import loadIndicators, CHARTFREQUENCIES
from .utils import parseQuarterYear, parseMonthYear, is_leap_year, parseSeriesFreqInputs, lowestFrequency



def parse(chart, chartFormat, name=None, first=None, last=None, freq=None, func=None, quiet=True):
    rawdata, title, subtitle = downloadChart(chart, first, last, quiet)


    '''
    Depending on chart format, we get the following:
        * t0 = date of first observation
        * T  = total number of observations
        * w  = data frequency in original rawdata
        * data = data where each time series is a column vector
    '''

    if chartFormat == 'YearMonth':
        t0, T, w = rawdata.index[0] + '/01', rawdata.size, 'M'
        data = rawdata.stack(dropna=False)
    elif chartFormat == 'MonthYear':
        if 'total' in str(rawdata.index[0]).lower():
            rawdata.drop(rawdata.index[0], inplace=True)
        t0, T, w = rawdata.columns[0] + '/01', rawdata.size, 'M'
        data = rawdata.transpose().stack(dropna=False)
    elif chartFormat == 'IndicatorYear':
        t0, T, w = rawdata.columns[0] + '/12', rawdata.shape[1], 'A'
        data = rawdata.transpose()
    elif chartFormat == 'IndicatorQuarter':
        t0, T, w = parseQuarterYear(rawdata.columns[0]), rawdata.shape[1], 'Q'
        data = rawdata.transpose()
    elif chartFormat == 'QuarterIndicator':
        t0, T, w = parseQuarterYear(rawdata.index[0]), rawdata.shape[0], 'Q'
        data = rawdata
    elif chartFormat == 'MonthIndicator':
        t0, T, w = parseMonthYear(rawdata.index[0]), rawdata.shape[0], 'M'
        data = rawdata
    elif chartFormat == 'IndicatorMonth':
        t0, T, w = parseMonthYear(rawdata.columns[0]), rawdata.shape[1], 'M'
        data = rawdata.transpose()
    elif chartFormat == 'DayYear':
        years = np.array([int(y) for y in rawdata.columns])
        nonleap = ~ is_leap_year(years)
        rawdata.iloc[59, nonleap] = np.inf  # row 59 = Feb 29 (counting from zero-base)
        rawdata = rawdata.transpose().stack(dropna=False)
        data = rawdata[rawdata != np.inf]
        t0, T, w = '%d/01/01' % years[0], data.size, 'D'
    else:
        return rawdata

    data.index = pd.date_range(start=t0, periods=T, freq=w)

    # Rename time series and drop missing values
    if isinstance(data, pd.Series):
        data.name = name if name else title
        data.dropna(inplace=True)
    elif isinstance(data, pd.DataFrame):
        data.columns = [name + txt for txt in data.columns]
        data = data.dropna(0, 'all').dropna(1, 'all')
    else:
        raise ValueError('Unexpected data type: %s' % type(data))

    # Resample data
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