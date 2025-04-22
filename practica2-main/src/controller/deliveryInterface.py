'''
Implementación de las funciones que procesan los mensajes de los repartidores.

Clases
------
DeliveryInterface
    Clase que actúa como consumidor asíncrono de la cola a la que se envían los 
    mensajes de los repartidores.
'''

import pika
import uuid

import request
from state import RequestState
from consumer import Consumer
from config import GID, D2X

class DeliveryInterface(Consumer):
    '''
    Clase que actúa como consumidor asíncrono de la cola a la que se envían los 
    mensajes de los repartidores.

    Extiende a la clase consumer.Consumer implementando el método de 
    procesamiento de los mensajes que se reciben de los repartidores.

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
        super().__init__(D2X, self.__on_consume)
        self.controller = controller

    def __on_consume(self, channel, method, properties, body):
        '''
        Función de callback para consumir los mensajes de los repartidores.

        Tokeniza el mensaje recibido y analiza el valor del primer token, que 
        puede ser 'DELIVERED' o 'DELIVERY_FAILED'. 
        
        Si es uno de ellos, llama al método correspondiente a la operación
        indicada por dicho token; y el resto de tokens se utilizan como 
        argumentos del método.

        Si no, el mensaje se descarta.
        '''

        tokens = body.decode().split()

        if len(tokens) < 2:
            print(f' [x] Mensaje no válido recibido: {body.decode()}')
            channel.basic_ack(delivery_tag=method.delivery_tag)
            return    

        try:
            req_id = uuid.UUID(tokens[1])
        except:
            print(f' [x] La id del pedido no es válida: {tokens[1]}')
            channel.basic_ack(delivery_tag=method.delivery_tag)
            return
        
        match tokens[0]:
            case 'DELIVERED':
                self.__delivered(channel, req_id)

            case 'DELIVERY_FAILED':
                self.__deliveryFailed(channel, req_id)

            case _:
                print(f' [x] Mensaje no válido recibido: {body.decode()}')
        
        channel.basic_ack(delivery_tag=method.delivery_tag)

    def __delivered(self, channel, req_id:uuid.UUID):
        '''
        Función de procesamiento de mensajes 'DELIVERED'.

        Utiliza la función updateRequest de Database para cambiar el estado del
        pedido a DELIVERED, si es posible.
        '''

        req = self.controller.db.updateRequest(req_id=req_id, update=request.on_deliver)
        if req is None:
            return
        
        if req.getState() == RequestState.DELIVERED:
            print(f' [✓] Pedido {req_id} entregado.')
        

    def __deliveryFailed(self, channel, req_id:uuid.UUID):
        '''
        Función de procesamiento de mensajes 'DELIVERY_FAILED'.

        Utiliza la función updateRequest de Database para cambiar el estado del
        pedido a FAILED, y si lo hace con éxito, envía el mensaje de aviso al
        cliente.
        '''

        req = self.controller.db.updateRequest(req_id=req_id, update=request.on_fail)
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