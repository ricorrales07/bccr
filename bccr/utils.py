import numpy as np
import pandas as pd
import re


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


def seriesAsDict(series):
    if isinstance(series, int):
        series = [series]

    alreadyDict = isinstance(series, dict)
    return series if alreadyDict else {chartNumber: '' for chartNumber in series}


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