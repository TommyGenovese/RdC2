# practica1

## Servidor web

Este proyecto implementa un servidor web, basado en HTTP.

## Instalación

El ejecutable se obtiene mediante la herramienta `make`. Basta con ejecutarla desde el directorio principal del proyecto una vez se han descargado los archivos:

```
make
```

También se puede compilar y ejecutar el programa con un único comando del makefile, mediante la siguiente instrucción:

```
make run
```

En cualquiera de los dos casos, se genera un ejecutable, **web_server**, en el directorio **bin/**, a su vez dentro del directorio principal del proyecto.

## Uso

El programa se puede lanzar, una vez compilado, simplemente ejecutando `./bin/web_server` desde el directorio principal del proyecto. 

No recibe argumentos de la línea de comandos, sino que todos los aspectos de configuración se modifican desde el fichero **server.conf**. Este fichero debe encontrarse en el mismo directorio del ejecutable.

## Fichero de configuración

El fichero de configuración debe llamarse **server.conf** y encontrarse en el mismo directorio que el ejecutable **web_server** para garantizar el funcionamiento del programa.

Además de los campos indicados en el enunciado, el fichero de configuración incluye otras dos opciones de configuración:

* `server_mode`: Indica si el servidor debe ejecutarse con un pool de hilos (`pool`), como un servidor reactivo (`reactive`) o como uno iterativo (`iterative`).

* `logger_path`: Indica la ruta del fichero de loggeo, relativa a la ruta del fichero de configuración. 

En el caso de `logger_path`, es un campo requerido por el programa para ejecutarse correctamente, y por lo tanto no se puede dejar en blanco. Por defecto, tiene el valor de **server.log** (y por lo tanto el fichero de loggeo se encuentra en el mismo directorio que el ejecutable).

El archivo de configuración entregado indica que el servidor utilizará el puerto 8080 para recibir peticiones, y atenderá a un máximo de 20 clientes simultáneamente; si bien estos datos se pueden modificar.

## Web

Se proporciona con la entrega algunos de los ficheros necesarios para probar el servidor con una web básica. Estos archivos se encuentan en el directorio **bin/www**, pues es la ruta indicada en el fichero de configuración.

La carpeta **media** no se ha incluido en la entrega debido al tamaño de la misma. Sin embargo, es necesaria para que la web se visualice adecuadamente, por la que deberá añadirse al directorio **www** con los archivos necesarios, que son al menos los siguientes:

* **animacion.gif**
* **documento.pdf**
* **documento.docx**
* **img_big.jpeg**
* **img_small.jpeg**
* desde **img1.jpg** hasta **img10.jpg**
* **texto.txt**
* **video.mpeg**

Se ha añadido un script de python de elaboración propia, **busca_strings.py**, para probar la ejecución de scripts. Se encuentra en la carpeta **scripts**, junto con el resto de scripts.

## Organización de archivos

Los archivos se han organizado como se sugiere en Moodle.

La carpeta **srclib** contiene los ficheros fuente de las librerías. Como la mayoría de la funcionalidad se ha distribuido en varias librerías, es donde se encuentran la mayoría de ficheros fuente, separados a su vez en un directorio para cada librería.

En **src** se encuentra el código del main del ejecutable.

Las carpetas **lib**, **obj**, **includes** y **bin** contienen las librerías ya compiladas, los objetos, los ficheros de cabecera y el ejecutable, respectivamente.