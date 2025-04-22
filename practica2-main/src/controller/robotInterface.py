'''
Implementación de las funciones que procesan los mensajes de los robots.

Clases
------
RobotInterface
    Clase que actúa como consumidor asíncrono de la cola a la que se envían los 
    mensajes de los robots.
'''

import pika
import uuid

import request
from state import RequestState
from consumer import Consumer
from config import HOST, GID, R2X, X2D

class RobotInterface(Consumer):
    '''
    Clase que actúa como consumidor asíncrono de la cola a la que se envían los 
    mensajes de los robots.

    Extiende a la clase consumer.Consumer implementando el método de 
    procesamiento de los mensajes que se reciben de los robots.

    Parámetros
    ----------
    controller : Controller
        Controlador del sistema, es el objeto que crea una instancia de esta
        interfaz, e inicia y detiene su ejecución.

    Atributos
    ---------
    controller : Controller
        Referencia al parámetro controller.
    '''

    def __init__(self, controller) -> None:
        super().__init__(R2X, self.__on_consume)
        self.controller = controller
        self.__declareAnswerQueue()

    def __declareAnswerQueue(self):
        '''
        Declara la cola del controlador al repartidor para asegurar su 
        existencia al lanzar el controlador.

        Se define en esta clase porque es la que trabaja con dicha cola.
        '''

        cn = pika.BlockingConnection(
            parameters=pika.ConnectionParameters(host=HOST)
        )
        ch = cn.channel()
        ch.queue_declare(X2D, durable=True)
        cn.close()

    def __on_consume(self, channel, method, properties, body):
        '''
        Función de callback para consumir los mensajes de los robots.

        Tokeniza el mensaje recibido y analiza el valor del primer token, que 
        puede ser 'MOVED' o 'NOT_FOUND'. 
        
        Si es uno de ellos, llama al método correspondiente a la operación
        indicada por dicho token; y el resto de tokens se utilizan como 
        argumentos del método.

        Si no, el mensaje se descarta.
        '''

        tokens = body.decode().split()

        if len(tokens) < 3:
            print(f' [x] Mensaje no válido recibido: {body.decode()}')
            channel.basic_ack(delivery_tag=method.delivery_tag)
            return    

        try:
            req_id = uuid.UUID(tokens[1])
        except:
            print(f' [x] La id del pedido no es válida: {tokens[1]}')
            channel.basic_ack(delivery_tag=method.delivery_tag)
            return
        
        product = request.Product(tokens[2])
        
        match tokens[0]:
            case 'MOVED':
                self.__moved(channel, req_id, product)

            case 'NOT_FOUND':
                self.__notFound(channel, req_id, product)

            case _:
                print(f' [x] Mensaje no válido recibido: {body.decode()}')
        
        channel.basic_ack(delivery_tag=method.delivery_tag)

    def __moved(self, channel, req_id:uuid.UUID, product):
        '''
        Función de procesamiento de mensajes 'MOVED'.

        Utiliza la función updateRequest de Database para cambiar el estado del
        producto a FOUND y el del pedido a IN_CONVEYOR. Si lo hace con éxito,
        solicita a los repartidores la entrega del pedido.
        '''

        if not self.controller.db.getRequest(req_id).stateIsTemporary():
            return
        
        req = self.controller.db.updateRequest(req_id=req_id, update=request.on_moved, args=(product,))
        if req is None:
            return
        
        if req.getState() == RequestState.IN_CONVEYOR:
            print(f' [✓] Pedido {req_id} en espera para ser entregado.')
            msg = f'DELIVERY {req.requestInfo()}'
            channel.basic_publish(
                exchange='',
                routing_key=X2D,
                body=msg,
                properties=pika.BasicProperties(delivery_mode=2)
            )

    def __notFound(self, channel, req_id:uuid.UUID, product):
        '''
        Función de procesamiento de mensajes 'NOT_FOUND'.

        Utiliza la función updateRequest de Database para cambiar el estado del
        producto a NOT_FOUND y el del pedido a FAILED. Si lo hace con éxito,
        avisa al cliente del fallo del pedido.
        '''

        if not self.controller.db.getRequest(req_id).stateIsTemporary():
            return
        
        req = self.controller.db.updateRequest(req_id=req_id, update=request.on_notFound, args=(product,))
        if req is None:
            return
        
        if req.getState() == RequestState.FAILED:
            print(f' [x] Pedido {req_id} fallido.')
            msg = f'REQUEST_FAILED {req_id}'
            channel.basic_publish(
                exchange='',
                routing_key=GID + req.getClient(),
                body=msg,
                properties=pika.BasicProperties(delivery_mode=2)
            )