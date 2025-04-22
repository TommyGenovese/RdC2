'''
Implementación de las funciones que procesan los mensajes de los clientes.

Clases
------
ClientInterface
    Clase que actúa como consumidor asíncrono de la cola a la que se envían los 
    mensajes de los clientes.
'''

import pika
import uuid

from state import ClientState, RequestState
import request
from consumer import Consumer
from config import HOST, GID, C2X, X2R

class ClientInterface(Consumer):
    '''
    Clase que actúa como consumidor asíncrono de la cola a la que se envían los 
    mensajes de los clientes.

    Extiende a la clase consumer.Consumer implementando el método de 
    procesamiento de los mensajes que se reciben de los clientes.

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
        super().__init__(C2X, self.__on_consume)
        self.controller = controller
        self.__declareAnswerQueue()
    
    def __declareAnswerQueue(self):
        '''
        Declara la cola del controlador al robot para asegurar su existencia al 
        lanzar el controlador.

        Se define en esta clase porque es la que trabaja con dicha cola.
        '''
        
        cn = pika.BlockingConnection(
            parameters=pika.ConnectionParameters(host=HOST)
        )
        ch = cn.channel()
        ch.queue_declare(X2R, durable=True)
        cn.close()

    def __on_consume(self, channel, method, properties, body):
        '''
        Función de callback para consumir los mensajes de los clientes.

        Tokeniza el mensaje recibido y analiza el valor del primer token, que 
        puede ser 'SIGN_UP', 'SIGN_IN', 'SIGN_OUT', 'REQUEST', 'CANCEL' o 
        'VIEW'. 
        
        Si es uno de ellos, llama al método correspondiente a la operación
        indicada por dicho token; y el resto de tokens se utilizan como 
        argumentos del método.

        Si no, el mensaje se descarta.
        '''

        tokens = body.decode().split()

        match tokens[0]:
            case 'SIGN_UP':
                if len(tokens) < 2:
                    print(f' [x] Mensaje no válido recibido: {body.decode()}')
                    channel.basic_ack(delivery_tag=method.delivery_tag)
                    return
                
                user_id = tokens[1]
                self.__signup(channel, user_id)
                
            case 'SIGN_IN':
                if len(tokens) < 2:
                    print(f' [x] Mensaje no válido recibido: {body.decode()}')
                    channel.basic_ack(delivery_tag=method.delivery_tag)
                    return
                
                user_id = tokens[1]
                self.__signin(channel, user_id)
            
            case 'SIGN_OUT':
                if len(tokens) < 2:
                    print(f' [x] Mensaje no válido recibido: {body.decode()}')
                    channel.basic_ack(delivery_tag=method.delivery_tag)
                    return
                
                user_id = tokens[1]
                self.__signout(channel, user_id)
                
            case 'REQUEST':
                if len(tokens) < 3:
                    print(f' [x] Mensaje no válido recibido: {body.decode()}')
                    channel.basic_ack(delivery_tag=method.delivery_tag)
                    return
                
                user_id = tokens[1]
                products = request.productsFromString(' '.join(tokens[2:]))
                self.__request(channel, user_id, products)
                
            case 'CANCEL':
                if len(tokens) < 3:
                    print(f' [x] Mensaje no válido recibido: {body.decode()}')
                    channel.basic_ack(delivery_tag=method.delivery_tag)
                    return
                
                user_id = tokens[1]
                try:
                    req_id = uuid.UUID(tokens[2])
                except:
                    print(f' [x] La id del pedido no es válida: {tokens[2]}')
                    msg = f'CANCEL_FAILED {tokens[2]}'
                    channel.basic_publish(
                        exchange='',
                        routing_key=GID + user_id,
                        body=msg,
                        properties=pika.BasicProperties(delivery_mode=2)
                    )
                    channel.basic_ack(delivery_tag=method.delivery_tag)
                    return
                
                self.__cancel(channel, user_id, req_id)

            case 'VIEW':
                if len(tokens) < 2:
                    print(f' [x] Mensaje no válido recibido: {body.decode()}')
                    channel.basic_ack(delivery_tag=method.delivery_tag)
                    return
                
                user_id = tokens[1]
                self.__view(channel, user_id)
                
            case _:
                print(f' [x] Mensaje no válido recibido: {body.decode()}')
        
        channel.basic_ack(delivery_tag=method.delivery_tag)

    def __signup(self, channel, user_id:str):
        '''
        Función de procesamiento de mensajes 'SIGN_UP'.

        Utiliza la función registerClient de Database para añadir un cliente a
        la base de datos. 

        Si lo hace con éxito, responde con mensaje 'SIGNED_UP'; si no, responde
        con 'SIGN_UP_FAILED'.
        '''

        if self.controller.db.registerClient(user_id) != 1:
            msg = 'SIGN_UP_FAILED'
            print(f' [x] El usuario {user_id} ya existe.')
        else:
            msg = 'SIGNED_UP'
            print(f' [✓] Usuario {user_id} registrado.')
        
        channel.basic_publish(
            exchange='',
            routing_key=GID + user_id,
            body=msg,
            properties=pika.BasicProperties(delivery_mode=2)
        )
    
    def __signin(self, channel, user_id:str):
        '''
        Función de procesamiento de mensajes 'SIGN_IN'.

        Utiliza la función updateClient de Database para cambiar el estado de un
        cliente a SIGNED_IN.

        Si lo hace con éxito, responde con mensaje 'SIGNED_IN'; si no, responde
        con 'SIGN_IN_FAILED'.
        '''

        if self.controller.db.updateClient(user_id, ClientState.SIGNED_IN) != 1:
            msg = 'SIGN_IN_FAILED'
            print(f' [x] Usuario inválido')
        else:
            msg = 'SIGNED_IN'
            print(f' [✓] Sesión iniciada como {user_id}.')
        
        channel.basic_publish(
            exchange='',
            routing_key=GID + user_id,
            body=msg,
            properties=pika.BasicProperties(delivery_mode=2)
        )
    
    def __signout(self, channel, user_id:str):
        '''
        Función de procesamiento de mensajes 'SIGN_OUT'.

        Utiliza la función updateClient de Database para cambiar el estado de un
        cliente a SIGNED_OUT.

        Si lo hace con éxito, responde con mensaje 'SIGNED_OUT'; si no, responde
        con 'SIGN_OUT_FAILED'.
        '''

        if self.controller.db.updateClient(user_id, ClientState.SIGNED_OUT) != 1:
            msg = 'SIGN_OUT_FAILED'
            print(f' [x] Usuario inválido')
        else:
            msg = 'SIGNED_OUT'
            print(f' [✓] Sesión de {user_id} cerrada')
        
        channel.basic_publish(
            exchange='',
            routing_key=GID + user_id,
            body=msg,
            properties=pika.BasicProperties(delivery_mode=2)
        )

    def __request(self, channel, user_id:str, products:list[request.Product]):
        '''
        Función de procesamiento de mensajes 'REQUEST'.

        Utiliza la función addRequest de Database para añadir un pedido a
        la base de datos. 

        Si lo hace con éxito, responde con mensaje 'REQUEST_CREATED'; si no, 
        responde con 'REQUEST_FAILED'.
        '''

        req = request.Request(user_id, products)
        
        if self.controller.db.addRequest(req) <= 0:
            msg = 'REQUEST_FAILED'
            channel.basic_publish(
                exchange='',
                routing_key=GID + user_id,
                body=msg,
                properties=pika.BasicProperties(delivery_mode=2)
            )
            return
        
        print(f' [✓] Pedido creado: {req}')
        msg = 'REQUEST_CREATED ' + req.requestInfo().partition(' ')[2]
        channel.basic_publish(
            exchange='',
            routing_key=GID + user_id,
            body=msg,
            properties=pika.BasicProperties(delivery_mode=2)
        )

        for p in products:
            msg = f'MOVE {req.getId()} {p.getName()}'
            channel.basic_publish(
                exchange='',
                routing_key=X2R,
                body=msg,
                properties=pika.BasicProperties(delivery_mode=2)
            )

    def __cancel(self, channel, user_id:str, req_id:uuid.UUID):
        '''
        Función de procesamiento de mensajes 'CANCEL'.

        Utiliza la función updateRequest de Database para cambiar el estado de 
        un pedido a CANCELLED.

        Si lo hace con éxito, responde con mensaje 'CANCELLED'; si no, responde
        con 'CANCEL_FAILED'.
        '''

        if self.controller.db.getClientState(user_id) != ClientState.SIGNED_IN:
            msg = f'CANCEL_FAILED {req_id}'
            print(f' [x] No se ha iniciado la sesión de {user_id}.')
            channel.basic_publish(
                exchange='',
                routing_key=GID + user_id,
                body=msg,
                properties=pika.BasicProperties(delivery_mode=2)
            )
            return
        
        req = self.controller.db.getRequest(req_id)
        if req is None:
            msg = f'CANCEL_FAILED {req_id}'
            channel.basic_publish(
                exchange='',
                routing_key=GID + user_id,
                body=msg,
                properties=pika.BasicProperties(delivery_mode=2)
            )
            return
        
        if not req.stateIsTemporary():
            msg = f'CANCEL_FAILED {req_id}'
            print(f' [x] El pedido no se puede cancelar.')
            channel.basic_publish(
                exchange='',
                routing_key=GID + user_id,
                body=msg,
                properties=pika.BasicProperties(delivery_mode=2)
            )
            return
        
        req = self.controller.db.updateRequest(update=request.on_cancel, req_id=req_id, user_id=user_id)
        
        if req is None:
            msg = f'CANCEL_FAILED {req_id}'
        elif req.getState() != RequestState.CANCELLED:
            msg = f'CANCEL_FAILED {req_id}'
            print(f' [x] El pedido no se puede cancelar.')
        else:
            msg = f'CANCELLED {req_id}'
            print(f' [✓] Pedido {req_id} cancelado.')

        channel.basic_publish(
            exchange='',
            routing_key=GID + user_id,
            body=msg,
            properties=pika.BasicProperties(delivery_mode=2)
        )

    def __view(self, channel, user_id:str):
        '''
        Función de procesamiento de mensajes 'VIEW'.

        Utiliza la función getClientRequests de Database para ver todos los
        pedidos de un cliente.

        Si lo hace con éxito, responde con mensaje 'FOUND_REQUESTS'; si no, 
        responde con 'VIEW_FAILED'.
        '''
        
        if self.controller.db.getClientState(user_id) != ClientState.SIGNED_IN:
            msg = 'VIEW_FAILED'
            print(f' [x] No se ha iniciado la sesión de {user_id}.')
            channel.basic_publish(
                exchange='',
                routing_key=GID + user_id,
                body=msg,
                properties=pika.BasicProperties(delivery_mode=2)
            )
            return
        
        msg = 'FOUND_REQUESTS '
        for req in self.controller.db.getClientRequests(user_id):
            msg += '\n' + str(req).partition(' ')[2]
        
        channel.basic_publish(
            exchange='',
            routing_key=GID + user_id,
            body=msg,
            properties=pika.BasicProperties(delivery_mode=2)
        )