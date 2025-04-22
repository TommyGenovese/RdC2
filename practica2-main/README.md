# practica2



## Marketplace

Este proyecto implementa la cadena logística de un marketplace mediante colas de
mensajes de RabbitMQ 

## Requerimientos

Para ejecutar la aplicación, es necesario tener instalada la librería `pika` de
Python. Además, la máquina en la que se ejecuta el controlador debe tener 
instalado SQLite y la librería `sqlite3` de Python. Si se utiliza como servidor 
de las colas de mensajes `localhost`, la máquina debe estar ejecutando RabbitMQ 
localmente.

## Fichero de configuración

El fichero **config.py** del directorio **src** define los nombres que se usarán
para la base de datos, el host y las colas de mensajes. Si se desea modificar el
nombre de alguno de estos elementos, solo hay que cambiar el valor de la 
constante correspondiente.

Es importante no cambiar el valor de `GID` ya que indica el número de la pareja
que ha realizado esta práctica, y cambiarlo puede causar conflictos con las 
colas de otras parejas si se usa el mismo host.

## Pruebas

Se han elaborado dos tipos de pruebas: scripts de prueba que ejecutan múltiples
instancias de los actores simulando situaciones reales, y test unitarios 
elaborados con el módulo `unittest` de Python.

Los test unitarios se han elaborado para los módulos `request` y 
`controller.database`, pues son los que contienen métodos públicos que se pueden
probar fácilmente con este tipo de test. Para probar el resto del código, se 
recomienda utilizar los scripts proporcionados.

## Organización de archivos

El código se encuentra en el directorio **src**, repartido en varios 
subdirectorios. El directorio **test** contiene los test unitarios para los 
módulos `request` y `controller.database`, **scripts** contiene los scripts de 
prueba con múltiples actores y **launchers** contiene los scripts de python para
lanzar a cada uno de los actores.

El paquete **client** contiene los módulos que implementan al cliente, y el
paquete **controller** contiene los módulos del controlador. El resto del código
fuente se encuentra en diversos módulos (archivos **.py**) en el propio 
directorio **src**.