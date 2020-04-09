# bccr

## Una API de Python para descargar datos del Banco Central de Costa Rica

El propósito de este paquete es proveer herramientas para buscar y descargar indicadores publicados por el [Banco Central de Costa Rica](https://www.bccr.fi.cr/).

El paquete ofrece dos clases para buscar datos y descargarlos:

* [`ServicioWeb`](http://randall-romero.com/demo-bccr-servicioweb/): descarga indicadores individuales del [servicio web](https://www.bccr.fi.cr/seccion-indicadores-economicos/servicio-web) del Banco Central.
* [`PaginaWeb`](http://randall-romero.com/demo-bccr-paginaweb/): descarga cuadros individuales (algunos con un solo indicador, otros con varios), de la página de [indicadores económicos](https://www.bccr.fi.cr/seccion-indicadores-economicos/indicadores-económicos).

Independientemente de la clase utilizada, los datos se descargan y se presentan en una tabla de `pandas`, en la cual cada fila corresponde a un período (día, mes, trimestre, año) y cada columna a un indicador. 

### Breves indicaciones acerca del uso del paquete
Las API de ambas clases son similares. En esencia, se crea un objeto consulta

    consulta = bccr.ServicioWeb()
 
 o bien 
 
     consulta = bccr.PaginaWeb()

Para buscar los códigos de los indicadores

    consulta.buscar(frase="descripción contiene esta frase exacta")
    consulta.buscar(todos="descripción tiene todas estas palabras")
    consulta.buscar(algunos="descripción tiene alguna de estas palabras")
    
Una vez conocidos los códigos de los indicadores, se descargan los datos con

    consulta(codigo1, codigo2, ..., codigoN)    

lo cual da por resultado una tabla de datos de [`pandas`](https://pandas.pydata.org/).


Este [video de YouTube](https://youtu.be/XLlr9XItfDE) contiene un tutorial acerca de cómo utilizar el paquete.

### Aviso

Este paquete no es un producto oficial de BCCR. El autor lo provee para facilitar el manejo de datos, pero no ofrece ninguna garantía acerca de su correcto funcionamiento. 


