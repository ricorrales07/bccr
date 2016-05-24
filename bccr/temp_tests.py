from bccr import *
# import matplotlib.pyplot as plt
# import seaborn


#print(downloadChart(125, 2012, 2015))

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

print(findAllCharts())

#print(api(9,2012, 2014))