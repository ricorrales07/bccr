from nose.tools import *
from bccr import *

def setup():
    print("SETUP!")

def teardown():
    print("TEAR DOWN!")
 
def test_basic():
    print("I RAN!")

def test_api():
     assert_in('CodCuadro=125', api(125))
     assert_in('FecInicial=2007/01/01', api(125, 2007))
     assert_in('FecFinal=2014/12/31', api(125, 2007, 2014))
     assert_not_in('Excel', api(125, 2007, 2014, excel=False))


def test_downloadChart():
    assert_equal(downloadChart(125)['V0'][0],  'Medio circulante (M1) medido a nivel del sistema bancario')



'''
#print(downloadChart(125, 2012, 2015))
#print(readYearMonth(125, 2012, 2015))
datos = readMonthYear({9: 'ipc', 289: 'ipc_nt'}, 2000, 2015, freq='Q')
#print(datos)
datos.plot(subplots=True)
plt.show()

print(readIndicatorYear(2980)['Producto interno bruto a precios básicos'])
#plt.show()
'''

if __name__ == '__main__':
   test_api()
   test_downloadChart()
