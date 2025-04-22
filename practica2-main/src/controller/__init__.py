'''
Implementación del controlador que gestiona el estado de los pedidos.

Este controlador recibe mensajes desde tres colas distintas, actualiza los
pedidos en función de dichos mensajes y emite mensajes de respuesta en caso
necesario.

Módulos
-------
clientInterface
    Implementación de las funciones que procesan los mensajes de los clientes.
deliveryInterface
    Implementación de las funciones que procesan los mensajes de los 
    repartidores.
robotInterface
    Implementación de las funciones que procesan los mensajes de los robots.
database
    Implementación de las funciones de acceso y actualización de la base de
    datos.

Clases
------
Controller
    Clase usada para representar al controlador y realizar sus funciones.
'''

import threading
import signal

from controller.clientInterface import ClientInterface
from controller.deliveryInterface import DeliveryInterface
from controller.robotInterface import RobotInterface
from controller.database import Database
from config import DB

class Controller:
    '''
    Clase usada para representar al controlador y realizar sus funciones.

    Atributos
    ---------
    db : database.Database
        Base de datos con la información del sistema (clientes, pedidos y
        productos con su correspondiente estado).
    clientInterface : clientInterface.ClientInterface
        Interfaz que recibe y procesa los mensajes de los clientes.
    robotInterface : robotInterface.RobotInterface
        Interfaz que recibe y procesa los mensajes de los robots.
    deliveryInterface : deliveryInterface.DeliveryInterface
        Interfaz que recibe y procesa los mensajes de los repartidores.
    threads : list[threading.Thread]
        Lista de referencias a los hilos en los que se ejecutan las interfaces.
    
    Métodos
    -------
    run()
        Lanza los hilos en los que se ejecutan las interfaces y espera a recibir
        la señal SIGINT.
    '''
    
    def __init__(self) -> None:
        self.db = Database(DB)

        self.clientInterface = ClientInterface(self)
        self.robotInterface = RobotInterface(self)
        self.deliveryInterface = DeliveryInterface(self)

        self.threads = list[threading.Thread]()
        self.threads.append(threading.Thread(target=self.clientInterface.run, name='ClientInterface'))
        self.threads.append(threading.Thread(target=self.robotInterface.run, name='RobotInterface'))
        self.threads.append(threading.Thread(target=self.deliveryInterface.run, name='DeliveryInterface'))

    def __signal_handler(self, signum, stack_frame):
        '''
        Función de manejo de la señal SIGINT.

        Detiene la ejecución de las interfaces y cierra la base de datos.
        '''

        print('')
        self.clientInterface.connection.ioloop.add_callback_threadsafe(
            callback=self.clientInterface.stop
        )
        self.robotInterface.connection.ioloop.add_callback_threadsafe(
            callback=self.robotInterface.stop
        )
        self.deliveryInterface.connection.ioloop.add_callback_threadsafe(
            callback=self.deliveryInterface.stop
        )
        for t in self.threads:
            t.join()
        
        self.db.close()

    def run(self):
        '''
        Lanza los hilos en los que se ejecutan las interfaces y espera a recibir
        la señal SIGINT.
        '''

        for t in self.threads:
            print(f' [*] Lanzando {t}')
            t.start()

        signal.signal(signalnum=signal.SIGINT, handler=self.__signal_handler)
        signal.pause()