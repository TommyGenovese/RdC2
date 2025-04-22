'''
Implementación del cliente que realiza los pedidos.

Ofrece a los usuarios una interfaz para registrase como clientes en el sistema,
iniciar/cerrar sesión, hacer pedidos, ver su estado y cancelarlos.

Módulos
-------
controllerInterface
    Implementación de las funciones que procesan los mensajes del controlador.

Clases
------
Client
    Clase usada para representar al cliente y realizar sus funciones.
'''

import pika
import threading

from state import ClientState
from client.controllerInterface import ControllerInterface
from config import HOST, GID, C2X

class Client:
    '''
    Clase usada para representar al cliente y realizar sus funciones.

    Parámetros
    ----------
    user_id : str
        Identificador del usuario que está usando la aplicación.
    cmd_line : bool, opcional
        Indica si se está usando una interfaz por línea de comandos.

    Atributos
    ---------
    user_id : str
        Referencia al parámetro user_id
    cmd_line : bool
        Referencia al parámetro cmd_line
    lock : threading.Lock
        Lock que regula el acceso de los hilos al estado del cliente.
    state : state.ClientState
        Estado actual del cliente.
    connection : pika.BlockingConnection
        Conexión utilizada para enviar comandos al controlador.
    channel : pika.channel.Channel
        Canal utilizado para enviar comandos al controlador.
    controllerInterface : controllerInterface.ControllerInterface
        Interfaz que recibe y procesa los mensajes del controlador.
    listenerThread : threading.Thread
        Referencia al hilo en el que se ejecuta la interfaz.
    
    Métodos
    -------
    send(message)
        Envía message al controlador.
    sign_up()
        Envía mensaje de SIGN_UP (registro en el sistema).
    sign_in()
        Envía mensaje de SIGN_IN (inicio de sesión).
    sign_out()
        Envía mensaje de SIGN_OUT (cierre de sesión).
    request(products)
        Envía mensaje REQUEST solicitando los productos de products.
    view()
        Envía mensaje de VIEW (ver los pedidos).
    cancel(req_id)
        Envía mensaje CANCEL solicitando cancelar el pedido con id req_id.
    stop()
        Detiene la ejecución de controllerInterface, recoge el hilo y cierra la 
        conexión con RabbitMQ.
    '''

    def __init__(self, user_id:str, cmd_line:bool = False):
        self.user_id = user_id
        self.cmd_line = cmd_line
        self.lock = threading.Lock()
        self.state = ClientState.NOT_REGISTERED

        # Para el envío de mensajes
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(HOST))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=C2X, durable=True)

        # Para la recepción de mensajes
        self.controllerInterface = ControllerInterface(GID + self.user_id, self)
        self.listenerThread = threading.Thread(target=self.controllerInterface.run)
        self.listenerThread.start()

    def send(self, message):
        '''
        Envía message al controlador.

        Parámetros
        ----------
        message : str
            El mensaje a enviar.
        '''

        self.channel.basic_publish(
            exchange='',
            routing_key=C2X,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2 
            )
        )

    def sign_up(self):
        '''
        Envía mensaje de SIGN_UP (registro en el sistema).
        '''

        self.send(f'SIGN_UP {self.user_id}')

    def sign_in(self):
        '''
        Envía mensaje de SIGN_IN (inicio de sesión).
        '''

        self.send(f'SIGN_IN {self.user_id}')
    
    def sign_out(self):
        '''
        Envía mensaje de SIGN_OUT (cierre de sesión).
        '''

        self.send(f'SIGN_OUT {self.user_id}')

    def request(self, products):
        '''
        Envía mensaje REQUEST solicitando los productos de products.
        
        Parámetros
        ----------
        products : list[str]
            Lista con los nombres de los productos que el pedido debe incluir.
        '''
        
        prod_string = ' '.join(products)
        self.send(f'REQUEST {self.user_id} {prod_string}')

    def view(self):
        '''
        Envía mensaje de VIEW (ver los pedidos).
        '''
        
        self.send(f'VIEW {self.user_id}')

    def cancel(self, req_id):
        '''
        Envía mensaje CANCEL solicitando cancelar el pedido con id req_id.
        
        Parámetros
        ----------
        req_id : str
            Identificador del pedido a cancelar.
        '''
        
        self.send(f'CANCEL {self.user_id} {req_id}')
    
    def stop(self):
        '''
        Detiene la ejecución de controllerInterface, recoge el hilo y cierra la 
        conexión con RabbitMQ.
        '''
        
        self.controllerInterface.connection.ioloop.add_callback_threadsafe(
            callback=self.controllerInterface.stop
        )
        self.listenerThread.join()
        self.connection.close()
