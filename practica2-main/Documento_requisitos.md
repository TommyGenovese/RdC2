
# Índice
1. [Introdución](#introduccion)
2. [Definición del proyecto](#definicion)
3. [Conclusiones](#solucion)
3. [Conclusiones](#conclusiones)


# 1. Introducción
El objetivo de Saimazoom es el de crear un sistema para la gestión de pedidos online. Este sistema debe incluir a los actores:
* **Cliente**, que realiza y gestiona pedidos de productos.
* **Controlador** central, que gestiona todo el proceso.
* **Robots**, que se encargan de buscar los productos en el almacén y colocarlos en las cintas transportadoras.
* **Repartidores**, encargados de transportar el producto a la casa del cliente
* **Admin** encargados de gestionar la base de datos del controlador central

El sistema debe de gestionar las interacciones entre todos estos actores, para las comunicaciones correspondientes se empleará una cola de mensajes.


# 2. Definición del proyecto
El sistema Saimazoom, como conjunto, debe gestionar pedidos, en los que los **clientes** pueden solicitar un producto. Una vez recibido un pedido, el **controlador** debe avisar a un **robot**, que mueve dicho producto del almacén a la cinta transportadora. Una vez en la cinta transportadora, el controlador avisa a un **repartidor**, que lleva el producto a la casa del **cliente**. 
<!-- Las comunicaciones pertinentes entre estos elementos estarán gestionadas por un **controlador** central, que mantiene la comunicación entre los **clientes**, **robots** y **repartidores**. -->

## 2.1. Objetivos y funcionalidad
Los objetivos principales son: 
* La gestión de los pedidos de los **clientes**, que pueden hacer, ver  y cancelar pedidos.
* La gestión de los **robots**, que reciben ordenes de de transportar los productos del almacen a la cinta transportadora.
* La gestión de los **repartidores**, que reparten los productos que hay en la cinta transportadora a la casa de los clientes.
* La gestión del **controlador** central, que tiene que mantener un control de productos, **clientes**, **robots** y **repartidores**. Tiene que guardar también los pedidos, con sus estados, que dependen de la relación con el resto de actores.
* La comunicación entre el **controlador** y el resto de actores

Para cumplir estos objetivos es necesario desarrollar una serie de funcionalidades básicas:
1. Registro de **Cliente**: registro desde una petición de un **Cliente** con un identificador de **cliente** que tiene que ser único.
2. Registro de Pedido: registro en la base de datos del **controlador** central con un id de **cliente** y de producto, también le asigna un estado al pedido.
3. Recepción de pedidos de los **Clientes**: hay que recibir y guardar los pedidos a realizar que están asociados a un **Cliente** y a un producto.
4. Asignación de trabajo a los **Robots**: hay que asignar a los **robots** las tareas de transporte de productos correspondientes a pedidos.
5. Asignación de trabajo a los **Repartidores**: hay que asignar a los **repartidores** las tareas de transporte de productos correspondientes a pedidos.

## 2.2. Requisitos
Nos limitaremos a los requisitos funcionales, estos los podemos dividir en los siguientes apartados:

### 2.2.1. **Lógica de clientes**
**LoCl1**. Registro en la aplicación en el que se recibe confirmación  
**LoCl2**. Realizar un pedido, en el que se pide un producto  
**LoCl3**. Pedir una lista de los pedidos realizados en la que se incluya id del producto correspondiente al pedido y estado del pedido  
**LoCl4**. Pedir la cancelación de un pedido



# 3. Implementación

A continuación se detallan algunas decisiones de diseño que se han tomado a lo largo de la práctica.

## Descripción de los mensajes

En la siguiente tabla se recogen los mensajes que se intercambian los agentes de la aplicación. Se identifica con una letra cada tipo de agente: C para el cliente, X para el controlador, R para el robot y P para el repartidor.

| Mensaje | De | A | Argumentos | Descripción |
|---------|:--:|:-:|------------|-------------|
|`SIGN_UP`| C | X | `user_id` | Resgistra un nuevo usuario identificado por `user_id` |
|`SIGN_UP_FAILED`| X | C | - | Indica fallo en el registro de un usuario |
|`SIGNED_UP`| X | C | - | Indica éxito en el registro de un usuario |
|`SIGN_IN`| C | X | `user_id` | Inicia la sesión del usuario `user_id` |
|`SIGN_IN_FAILED`| X | C | - | Indica fallo en el inicio de sesión |
|`SIGNED_IN`| X | C | - | Indica éxito en el inicio de sesión |
|`SIGN_OUT`| C | X | `user_id` | Cierra la sesión del usuario `user_id` |
|`SIGN_OUT_FAILED`| X | C | - | Indica fallo en el cierre de sesión |
|`SIGNED_OUT`| X | C | - | Indica éxito en el cierre de sesión |
|`REQUEST`| C | X | `user_id p1 [...]` | Realiza un pedido de los productos `p1` ...  a nombre de `user_id` |
|`REQUEST_CREATED`| X | C | `req_id p1 [...]` | Indica éxito en la creación de un nuevo pedido con identificador `req_id` |
|`REQUEST_FAILED`| X | C | `[req_id]` | Indica que un pedido (identificado por `req_id` si el pedido ya se había creado) no se puede completar |
| `CANCEL` | C | X | `user_id req_id` | Solicita la cancelación del pedido `req_id` del usuario `user_id` |
| `CANCELLED` | X | C | `req_id` | Confirma la cancelación del pedido dado por `req_id` |
| `CANCEL_FAILED` | X | C | `req_id` | Indica fallo en la cancelación del pedido dado por `req_id` |
| `VIEW` | C | X | `user_id` | Solicita ver todos los pedidos del cliente `user_id` |
| `FOUND_REQUESTS` | X | C | `[req_id1 p1_1 [...] ...]` | Muestra los pedidos encontrados con su `req_id` y sus productos |
| `VIEW_FAILED` | X | C | - | Indica fallo en la solicitud de los pedidos |
| `MOVE` | X | R | `req_id product` | Solicita la búsqueda de `product` para el pedido `req_id` a un robot |
| `MOVED` | R | X | `req_id product` | Confirma que se ha encontrado y movido a la cinta `product` para el pedido `req_id` |
| `NOT_FOUND` | R | X | `req_id product` | Indica que no se ha encontrado `product` para el pedido `req_id` |
| `DELIVERY` | X | P | `user_id req_id p1 [...]` | Solicita que se reparta el pedido identificado por `req_id` con productos `p1` ...  al usuario `user_id`|
| `DELIVERED` | P | X | `req_id` | Indica éxito en el reparto del pedido `req_id` |
| `DELIVERY_FAILED` | P | X | `req_id` | Indica fallo en el reparto del pedido `req_id` |
| `RECEIVE` | P | C | `req_id p1 [...]` | Entrega el pedido `req_id` al cliente |

## Diagrama de clases

![Diagrama de clase](images/DiagramaClases.png)

La clase `Consumer` implementa funcionalidad básica de un consumidor de una cola
de mensajes en un entorno multihilo, aplicando una misma función de consumo a 
todos los mensajes recibidos por dicha cola. Esto es útil para el cliente 
(`Client`) y el controlador (`Controller`).

El cliente tiene un hilo para leer de la terminal y enviar mensajes al 
controlador, y otro para recibir mensajes del controlador. Este último ejecuta 
el método `run` de una instancia de `ControllerInterface`, que hereda de
`Consumer`. De forma parecida, el controlador recibe mensajes desde tres colas 
distintas (una para mensajes de clientes, otra para mensajes de robots y otra
para mensajes de repartidores). Para ello se usan tres hilos que ejecutan
instancias de `ClientInterface`, `RobotInterface` y `DeliveryInterface`,
respectivamente. Cada una de estas 'interfaces' define la función de consumo de
mensajes que se aplica a los mensajes recibidos por las respectivas colas.

El controlador tiene además un atributo de clase `Database`, que permite acceder
a la base de datos con la información que hay en el sistema sobre clientes,
pedidos y productos. Por cada mensaje que recibe el controlador y que produce un 
cambio en uno de esos elementos, se actualiza la base de datos de manera 
adecuada, de forma que al cerrar la aplicación el sistema ya está actualizado.

Para representar los pedidos y sus productos, el sistema utiliza instancias de
las clases `Request` y `Product`, respectivamente. Junto con las enumeraciones
de estados `RequestState` y `ProductState`, permiten definir las transiciones de
estados posibles en estos elementos, así como almacenar su información en la 
base de datos. También se usa una enumeración para el estado del cliente,
`ClientState`, para saber si está o no registrado, y si ha iniciado sesión o no.

Finalmente, las clases `Robot` y `Delivery` implementan a los robots y los 
repartidores, respectivamente. Las instancias de estas dos clases, y las de la
clase `Ccontroller`, se ponen en funcionamiento al llamar a su método run, y se
detienen mediante una interrupción de teclado.

En el caso del cliente, la recepción de mensajes se inicia al crear la 
instancia, y el envío de mensajes se realiza a través de los métodos de la clase
`Client`. La ejecución se detiene al llamar al método `stop`. Se recomienda usar
el script `commandline_client.py` del directorio **launchers**, que permite
simular al cliente a través de la línea de comandos. 

## Diagrama de estados de un pedido

En este apartado se presenta el diagrama de estados correspondiente a los estados por los que pasa un pedido (`Request`).

![Diagrama de estados](images/DiagramaEstados.png)

El estado `IN_STORAGE` representa el estado del paquete mientras los robots
buscan sus productos, pudiendo cancelarse. El estado `IN_CONVEYOR` representa
el paquete con todos los productos listo para el envío, y ya no puede cancelarse.
Los estados `CANCELLED`, `FAILED` y `DELIVERED` representan si un paquete ha 
sido cancelado, no se ha podido entregar o se ha entregado correctamente,
respectivamente.

## Casos de uso

### Caso de uso 1: Pedido completado correctamente

* Actores involucrados: Controlador, Cliente, Robot, Repartidor.
* Actor principal: Controlador.
* Resumen: El cliente realiza un pedido, y el controlador lo gestiona hasta que es entregado al cliente.
* Precondiciones: 
    1. El cliente está registrado y ha iniciado sesión.
    2. Hay al menos un robot conectado al sistema.
    3. Hay al menos un repartidor conectado al sistema.
* Postcondiciones: 
    1. Se registra la entrega correcta del pedido actualizando su estado a `DELIVERED`.
    2. El cliente recibe el pedido en forma de mensaje.
* Curso básico de eventos:
    1. El cliente envía un mensaje `REQUEST` con el listado de productos que pide.
    2. El controlador crea un nuevo objeto `Request` con la información recibida.
    3. El controlador confirma la creación del pedido con un mensaje `REQUEST_CREATED` para el cliente.
    4. El controlador solicita a los robots que empaqueten los productos con un mensaje `MOVE` para cada producto.
    5. Los robots confirman el empaquetamiento de cada producto con un mensaje `MOVED`.
    6. Cuando se han empaquetado todos los productos, el controlador actualiza el estado del paquete a `IN_CONVEYOR`.
    7. El controlador solicita a los repartidores el reparto del pedido con un mensaje `DELIVERY`.
    8. El repartidor entrega el paquete al cliente mediante un mensaje `RECEIVE` y confirma la entrega al controlador mediante un mensahe `DELIVERED`.
    9. El controlador actualiza el estado del pedido a `DELIVERED`.
* Caminos alternativos:
    1. El listado de productos está vacío y el controlador envía un mensaje `REQUEST_FAILED` al cliente.
    2. Uno de los robots no encuentra un producto: ver caso de uso 2.
    3. El cliente cancela el pedido antes de que se empaqueten los productos: ver caso de uso 3.
    4. 1. El repartidor falla los tres intentos de reparto y avisa al controlador mediante un mensaje `DELIVERY_FAILED`.
       2. El controlador actualiza el estado del pedido a `FAILED`.
       3. El controlador avisa al cliente con un mensaje `REQUEST_FAILED`.
* Observaciones: el éxito o fallo al buscar un producto y al entregar un pedido se simulan utilizando unas probabilidades asociadas a las clases `Robot` y `Delivery`, respectivamente, y haciendo uso del módulo `random` de Python.

### Caso de uso 2: Pedido en el que no se encuentra un producto

* Actores involucrados: Controlador, Cliente, Robot.
* Actor principal: Controlador.
* Resumen: El cliente realiza un pedido, y el controlador lo gestiona hasta que uno de los productos no se encuentra y se declara el pedido como fallido.
* Precondiciones: 
    1. El cliente está registrado y ha iniciado sesión.
    2. Hay al menos un robot conectado al sistema.
* Postcondiciones: 
    1. Se registra el fallo del pedido pedido actualizando su estado a `FAILED`.
    2. El cliente recibe un aviso informando del fallo.
* Curso básico de eventos:
    1. El cliente envía un mensaje `REQUEST` con el listado de productos que pide.
    2. El controlador crea un nuevo objeto `Request` con la información recibida.
    3. El controlador confirma la creación del pedido con un mensaje `REQUEST_CREATED` para el cliente.
    4. El controlador solicita a los robots que empaqueten los productos con un mensaje `MOVE` para cada producto.
    5. Uno de los robots no encuentra el producto e informa al controlador mediante un mensaje `NOT_FOUND`.
    6. El controlador actualiza el estado del pedido a `FAILED`.
    7. El controlador informa al cliente con un mensaje `REQUEST_FAILED`.
* Caminos alternativos:
    1. El listado de productos está vacío y el controlador envía un mensaje `REQUEST_FAILED` al cliente.
* Observaciones: el éxito o fallo al buscar un producto se simula utilizando una probabilidad asociada a la clase `Robot` y haciendo uso del módulo `random` de Python.

### Caso de uso 3: Pedido cancelado por el cliente

* Actores involucrados: Controlador, Cliente.
* Actor principal: Controlador.
* Resumen: El cliente realiza un pedido, y el controlador lo gestiona hasta que el cliente lo cancela.
* Precondiciones: 
    1. El cliente está registrado y ha iniciado sesión.
* Postcondiciones: 
    1. Se registra la cancelación del pedido pedido actualizando su estado a `CANCELLED`.
    2. El cliente recibe un aviso informando del éxito en la cancelación.
* Curso básico de eventos:
    1. El cliente envía un mensaje `REQUEST` con el listado de productos que pide.
    2. El controlador crea un nuevo objeto `Request` con la información recibida.
    3. El controlador confirma la creación del pedido con un mensaje `REQUEST_CREATED` para el cliente.
    4. El cliente solicita cancelar el pedido mediante un mensaje `CANCEL`.
    5. El controlador actualiza el estado del pedido a `CANCELLED`.
    6. El controlador informa al cliente de la cancelación del pedido a través de un mensaje `CANCELLED`.
* Caminos alternativos:
    1. El listado de productos está vacío y el controlador envía un mensaje `REQUEST_FAILED` al cliente.
    2. 1. La solicitud de cancelación llega tras pasar el pedido a estado `IN_CONVEYOR`.
       2. El controlador informa del fallo en la cancelación con un mensaje `CANCEL_FAILED`.
       3. La gestión del pedido continua como en el caso de uso 1.

# 4. Conclusiones
*A rellenar*
