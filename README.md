# bccr

Nota: la versión original de este paquete fue creada por Randall Romero (https://github.com/randall-romero). Esta versión solo agrega funcionalidad para usarlo detrás de un proxy corporativo.

## Una API de Python para descargar datos del Banco Central de Costa Rica

El propósito de este paquete es proveer herramientas para buscar y descargar indicadores publicados por el [Banco Central de Costa Rica](https://www.bccr.fi.cr/).

El paquete ofrece dos clases para buscar datos y descargarlos:

* [ServicioWeb](http://randall-romero.com/demo-bccr-servicioweb/): descarga indicadores individuales del [servicio web](https://www.bccr.fi.cr/indicadores-economicos/servicio-web) del Banco Central.
* [PaginaWeb](http://randall-romero.com/demo-bccr-paginaweb/): descarga cuadros individuales (algunos con un solo indicador, otros con varios), de la página de [indicadores económicos](https://www.bccr.fi.cr/indicadores-economicos).

Independientemente de la clase utilizada, los datos se descargan y se presentan en una tabla de `pandas`, en la cual cada fila corresponde a un período (día, mes, trimestre, año) y cada columna a un indicador. 

## Breves indicaciones acerca del uso del paquete
Las API de ambas clases son similares. En esencia, se crea un objeto consulta y se utiliza para buscar códigos de indicadores (los cuales difieren según se trate del Servicio Web o de la página de indicadores económicos).

Este [video de YouTube](https://youtu.be/eB8YCQ-nn1g) contiene un tutorial acerca de cómo utilizar el paquete.

### Usando ServicioWeb 

Primero importamos una instancia de `ServicioWeb` llamada `SW` 

    from bccr import SW      


Conociendo los códigos de los indicadores, se descargan los datos con

    SW(nombre1=codigo1, nombre2=codigo2, ..., nombreN=codigoN)    

En la línea anterior, `nombre1`, `nombre2`, y `nombreN` son los nombres que se desea dar a los indicadores, y `codigo1`, `codigo2`, y `codigoN` son números enteros que identifican a esos indicadores en el Servicio Web.

El resultado se presenta como una tabla de datos de [`pandas`](https://pandas.pydata.org/), en la que cada fila es un período (día,mes, trimestre, año) y cada columna un indicador, con nombres `[nombre1, nombre2, ..., nombreN]`. 

Para buscar los códigos de los indicadores se usa el método `buscar`:

    SW.buscar("descripción tiene todas estas palabras") 
    SW.buscar(frase="descripción contiene esta frase exacta")
    SW.buscar(algunos="descripción tiene alguna de estas palabras")

Además, para buscar cuentas relacionadas (por ejemplo, si se conoce el `codigo` del IMAE y se desea buscar los códigos de IMAE por actividad)

    SW.quien(codigo)
    SW.subcuentas(codigo)

### Usando PaginaWeb 
Importamos una instancia de PaginaWeb()
 
    from bccr import PW      

Para buscar los códigos de los indicadores

    PW.buscar(frase="descripción contiene esta frase exacta")
    PW.buscar(todos="descripción tiene todas estas palabras")
    PW.buscar(algunos="descripción tiene alguna de estas palabras")
    
Una diferencia importante con respecto al servicio web es que una página web se refiere a un cuadro publicado (que puede tener uno o más indicadores), mientras que un código de servicio web está asociado a un único indicador.

Una vez conocidos los códigos de los indicadores, se descargan los datos con

    PW(codigo1, codigo2, ..., codigoN)    

lo cual da por resultado una tabla de datos de [`pandas`](https://pandas.pydata.org/), con una estructura similar a la que da `SW`.


### Usando GUI

Este paquete también incluye una interfase gráfica, desarrollada con [dash](https://plotly.com/dash/) y utilizando `ServicioWeb`, que permite consultar los datos y descargarlos con botones, en formatos de Excel, Stata y CSV. Además, la interfase muestra la línea de comando de `SW` que ejecuta la consulta deseada (por ejemplo, para incluirla en un script posteriormente).

Para utilizar la interfase gráfica

    from bccr import GUI
    GUI()

Esto abrirá la interfase en su navegador de internet predeterminado.

## Aviso importante

Este paquete no es un producto oficial de BCCR. El autor lo provee para facilitar el manejo de datos, pero no ofrece ninguna garantía acerca de su correcto funcionamiento. 


