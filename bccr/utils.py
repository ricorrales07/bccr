import numpy as np
import pandas as pd
import re

def isColumnEmpty(x):
    return np.all(np.isnan(x))


def removeEmptyColumns(data):
    emptyColumns = data.apply(isColumnEmpty).values
    return data.iloc[:, ~emptyColumns] if np.any(emptyColumns) else data



def findFirstElement(pattern, stringList):
    idx = 0

    for element in list(stringList):
        if re.match(pattern, str(element)):
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
    elif isinstance(data, pd.DataFrame):
        data.columns = colnames
        data = data.applymap(fixCommas)
        data = removeEmptyColumns(data)

    else:
        raise NotImplemented

    return resample(data, freq, func)


def seriesAsDict(series):
    if isinstance(series, int):
        series = [series]

    alreadyDict = isinstance(series, dict)
    return series if alreadyDict else {chartNumber: '' for chartNumber in series}

