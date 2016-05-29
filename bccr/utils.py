import re
import numpy as np
import pandas as pd


def findFirstElement(pattern: str, stringList):
    idx = 0

    for element in list(stringList):
        if re.match(pattern, str(element), re.IGNORECASE):
            return idx
        else:
            idx += 1

    raise ValueError('No match found!')


def fixCommas(x):
    return float(x.replace(",", ".")) if isinstance(x, str) else x


def resample(series, freq, func):
    if func is None:
        func = np.mean
    return series.resample(freq).apply(func) if freq else series



def tidy(data, timeindex, freq, func, colnames):

    data.index = timeindex
    if isinstance(data, pd.Series):
        data = data.apply(fixCommas)
        data.name = colnames
        data.dropna(inplace=True)
    elif isinstance(data, pd.DataFrame):
        data.columns = colnames
        data = data.applymap(fixCommas).dropna(0, 'all').dropna(1, 'all')
        #data = removeEmptyColumns(data)

    else:
        raise NotImplemented

    return resample(data, freq, func)


def parseSeriesFreqInputs(series, func):

    # make a dictionary with series
    if isinstance(series, int):
        seriesdict = {series: ''}
    elif isinstance(series, pd.Series):
        seriesdict = dict(zip(series.index, series))
    elif isinstance(series, list) or isinstance(series, tuple):
        seriesdict = {chartNumber: '' for chartNumber in series}
    elif isinstance(series, dict):
        seriesdict = series
    else:
        raise ValueError('series must be integer, list of integers, dictionary, or pd.Series')

    # make a dictionary with functions
    if callable(func) or func is None:
        funcdict = {a: func for a in seriesdict.keys()}
    elif isinstance(func, dict):
        funcdict = {ch: (func[ch] if ch in func.keys() else None) for ch in seriesdict.keys()}
    else:
        raise ValueError('func must be a callable, None, or a dictionary of callables (chart: callable pairs)')

    return seriesdict, funcdict





def is_leap_year(years):
    """Determine whether a year is a leap year."""
    return np.bitwise_and(years % 4 == 0,
                          np.bitwise_or(years % 100 != 0,
                                        years % 400 == 0)
                          )


def parseQuarterYear(txt: str):
    """
        Parses a string of form 'trimestre 2/2014' into '2014/6'
    Parameters
    ----------
    txt :   A string with text and two integers, one representing the year and the other the quarter (1 to 4)

    Returns
    -------
        A string representing the last month of the quarter, in yyyy/mm format.
    """
    q0, year0 = [int(x) for x in re.findall("[-+]?\d+[\.]?\d*", txt)]
    if q0 not in range(1, 5):
        if year0 in range(1, 5):
            q0, year0 = year0, q0
        else:
            raise ValueError('Cannot identify the quarter')
    return '%d/%d' % (year0, 3*int(q0))


def parseMonthYear(txt: str):
    """
        Parses a string of form 'trimestre 2/2014' into '2014/6'
    Parameters
    ----------
    txt :   A string with text and two integers, one representing the year and the other the quarter (1 to 4)

    Returns
    -------
        A string representing the last month of the quarter, in yyyy/mm format.
    """
    year0 = [int(x) for x in re.findall("[-+]?\d+[\.]?\d*", txt)]

    return   #'%d/%d' % (year0, 3*int(q0))


MONTHS = {
    'Enero' : 1,
    'Febrero' : 2,
    'Marzo' : 3,
    'Abril' : 4,
    'Mayo' : 5,
    'Junio' : 6,
    'Julio' : 7,
    'Agosto' : 8,
    'Septiembre' : 9,
    'Octubre' : 10,
    'Noviembre' : 11,
    'Diciembre' : 12
}



def lowestFrequency(freqs):
    if 'A' in freqs:
        return 'A'
    if 'Q' in freqs:
        return 'Q'
    if 'M' in freqs:
        return 'M'
    if 'D' in freqs:
        return 'D'

    raise ValueError("Frequency must be any of 'A' (annual), 'Q' (quarterly), 'M' (monthly), or 'D' (daily)")

def findColumnTitles(data: pd.DataFrame):
    values = ~np.any(data.isnull().values, 1)
    return np.where(values)[0].min()


