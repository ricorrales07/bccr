import numpy as np
import pandas as pd

from .download import downloadChart
from .scrape import loadIndicators, CHARTFREQUENCIES
from .utils import parseQuarterYear, parseMonthYear, is_leap_year, parseSeriesFreqInputs, lowestFrequency



def parse(chart, chartFormat, name=None, first=None, last=None, freq=None, func=None, quiet=True):
    rawdata, title, subtitle = downloadChart(chart, first, last, quiet)
    varname = name if name else title

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
        h = 1 if 'total' in str(rawdata.index[0]).lower() else 0
        t0, T, w = rawdata.columns[0] + '/01', rawdata.size - 12 * h, 'M'
        data = rawdata.iloc[h:].transpose().stack(dropna=False)
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
    if chartFormat in ['MonthYear', 'YearMonth', 'DayYear']:
        data.name = varname
        data.dropna(inplace=True)
    elif chartFormat in ['IndicatorYear', 'IndicatorQuarter', 'IndicatorMonth', 'QuarterIndicator']:
        data.columns = [varname + txt for txt in data.columns]
        data = data.dropna(0, 'all').dropna(1, 'all')

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

    """

    seriesDict, funcdict = parseSeriesFreqInputs(series, func)
    indicators = loadIndicators().loc[list(seriesDict.keys()), 'function']
    indicators = indicators.apply(lambda x: x[4:])
    formats = dict(zip(indicators.index, indicators))

    if freq is None:
        original_frequencies = set([CHARTFREQUENCIES[k][0] for k in indicators['function']])
        if len(original_frequencies) > 1:
            freq = lowestFrequency(original_frequencies)
            print('\nDownloading data with frequencies : %s !!!' % original_frequencies)
            print('Returning frequency: %s\n' % freq)

    return pd.concat(
        [parse(chart, formats[chart], name, first, last, freq, funcdict[chart], quiet) for chart, name in seriesDict.items()],
        axis=1)