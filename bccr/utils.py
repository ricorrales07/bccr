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
    return float(x.replace(".", "").replace(",", ".")) if isinstance(x, str) else x


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
    month0 = MONTHS.apply(lambda x: bool(re.match(x, txt, re.IGNORECASE))).idxmax()
    year0 = re.findall("[-+]?\d+[\.]?\d*", txt)[0]
    return year0 + '/' + str(month0)


MONTHS = pd.Series(['Enero', 'Febrero','Marzo', 'Abril', 'Mayo', 'Junio',
                    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'],
                   index=range(1,13))

FREQS = pd.Series(range(4), index=['A', 'Q', 'M', 'D'])  # lower to higher frequencies


def lowestFrequency(freqs):
    original_frequencies = set([f[0].upper() for f in freqs])
    return FREQS[original_frequencies].argmin()


def findColumnTitles(data: pd.DataFrame):
    values = np.all(data.notnull().values, 1)
    return np.where(values)[0].min()

def parseDay(dia: str):
    '''
    Convert Spanish date to English date
    Parameters
    ----------
    dia String with Spanish date, format 'dd Mmm yyyy'

    Returns
    -------
    String with English date, format 'yyyy/mm/dd'
    '''
    meses = {'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04', 'may': '05', 'jun': '06',
            'jul': '07', 'ago': '08', 'set': '09', 'sep': '09', 'oct': '10', 'nov': '11', 'dic': '12'}

    d, m, y = dia.split()
    return y + '/' + meses[m[:3].lower()] + '/' + d


def columns_rename(db: pd.DataFrame):
    """
    Dictionary to rename columns
    Parameters
    ----------
    db pandas DataFrame

    Returns
    -------
    A string, code to make a dictionary to rename the columns of given dataframe
    """
    print('componentes = {')
    for x in db:
        print("'" + x + "': '',")
    print('}')


def parse_date_parameter(fecha, inicio=True):
    if type(fecha) is int:
        return str(fecha) + ('/01/01' if inicio else '12/31')
    elif type(fecha) is str:
        dig = re.findall('([0-9])', fecha)
        if len(dig)==8:
            return '/'.join(''.join(zz) for zz in (dig[:4], dig[4:6], dig[6:]))
        else:
            raise Exception('Formato de fecha no válido: Utilice "yyyy/mm/dd" para indicar fechas')
    else:
        raise Exception('Formato de fecha no válido: Utilice "yyyy/mm/dd" o un entero(yyyy) para indicar fechas')