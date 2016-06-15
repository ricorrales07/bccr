#print(downloadChart(125, 2012, 2015))
from bccr import *
import numpy as np

'''
print(api(125, 2010, 2015))
print(readYearMonth(125, 2012, 2015))
datos = readMonthYear({9: 'ipc', 289: 'ipc_nt'}, 2000, 2015, freq='Q')
#print(datos)
datos.plot(subplots=True)
plt.show()

'''

#print(readIndicatorYear(2980, quiet=False))
#plt.show()

#readTitle([125, 9, 289,9,9])

#print(readYearMonth([125, 138], 2012, 2015))
#print(readMonthYear([9, 289], freq='Q', quiet=False))
'''
print(api(9))
print(api(125, 2010))
print(api(289, 2010, 2015))
print(api(125, 2010, 2015, excel=False))
print(api(125, excel=False, open=True))

'''
#print(readIndicatorYear({189: 'Real__', 230: 'Nominal__'}))

#data = readDayYear([17, 367], quiet=False)
#data['2006-9':'2009-12'].plot(subplots=True)
#plt.show()

#print(findIndicators('export import', False))

#print(api(9,2012, 2014))
#print(readMonthYear([28, 29], quiet=False))

#readIndicatorQuarter(70, quiet=False).plot(subplots=True, layout=(-1, 3))
#plt.show()

#print(api(20, excel=True, open=True))

#print(read([28, 29], quiet=False))
#read(125)
#updateIndicators()


#downloadChart(125)

#search('precios')

#print(read([125, 19, 68, 70, 138, 367, 17], 2014, 2015, quiet=False))
#print(read([17, 19], 2014, 2015, freq='M', func={17:np.mean, 19:'last'}, quiet=False))

#print(read({8:'netas', 15:'brutas'}, quiet=False))

read([125, 17])
ipc = parse(2732,'MonthIndicator','IPC_')