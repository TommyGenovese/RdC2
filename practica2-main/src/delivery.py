'''
Implementación del repartidor que entrega los pedidos.

Este repartidor intenta entregar el pedido hasta un máximo de tres veces por
pedido.

El éxito o fallo al entregar el pedido se simula realizando una espera aleatoria
de entre 10 y 20 segundos, y después generando un número aleatorio entre 0 y 1
mediante el módulo random. Si este número es inferior a la probabilidad de
entrega definida en la clase Delivery, se determina que el intento ha sido
exitoso.

Clases
------
Delivery
    Clase usada para representar al repartidor y realizar sus funciones.
'''

import pika
import time
import random

from config import HOST, GID, X2D, D2X

class Delivery:
    '''
    Clase usada para representar al repartidor y realizar sus funciones.

    Atributos
    ---------
    p_entrega : float
        Probabilidad de que un intento de entrega sea exitoso.
    connection : pika.BlockingConnection
        Conexión con RabbitMQ.
    channel : pika.channel.Channel
        Canal de comunicación con RabbitMQ.
    
    Métodos
    -------
    run()
        Ejecuta el bucle de escuha y procesamiento de mensajes hasta que se 
        recibe la interrupción de teclado.
    '''

    p_entrega = 0.6
    '''Probabilidad de que un intento de entrega sea exitoso.'''

    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=HOST))
        self.channel = self.connection.channel()

        self.channel.queue_declare(X2D, durable=True)
        self.channel.queue_declare(D2X, durable=True)
        
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue=X2D, on_message_callback=self.__on_consume)

    def __on_consume(self, channel, method, properties, body):
        '''
        Función de callback para consumir los mensajes del controlador.

        Tokeniza el mensaje recibido y analiza el valor del primer token, que 
        solo puede ser 'DELIVERY'.
        
        Si lo es, realiza hasta un máximo de tres intentos de entrega del 
        pedido. En caso de éxito, informa al controlador y al cliente que
        realizó el pedido; en caso de fallo informa al controlador del fallo en 
        la entrega.

        Si no es 'DELIVERY', el mensaje se descarta.
        '''

        tokens = body.decode().split()
    
        if tokens[0] != 'DELIVERY':
            print(f' [x] Mensaje no válido recibido: {body.decode()}')
            channel.basic_ack(delivery_tag=method.delivery_tag)
            return
            
        if len(tokens) < 4:
            print(f' [x] Mensaje no válido recibido: {body.decode()}')
            channel.basic_ack(delivery_tag=method.delivery_tag)
            return
            
        user_id = tokens[1]
        req_id = tokens[2]
        products = tokens[3:]
        print(f' [*] Pedido {req_id} para {user_id} con productos: {products}')

        success = False
        for i in range(3):
            t = random.randint(10, 20)
            print(f' [*] Intento {i + 1}: ({t} seg)')
            time.sleep(t)
            if random.random() <= Delivery.p_entrega:
                success = True
                break
        
        products = ' '.join(products)
        if success:
            msg = 'DELIVERED ' + req_id
            print(f' [✓] {msg}')
            channel.basic_publish(
                exchange='', 
                routing_key=D2X, 
                body=msg,
                properties=pika.BasicProperties(delivery_mode=2)
            )
            msg = 'RECEIVE ' + req_id + ' ' + products
            channel.basic_publish(
                exchange='', 
                routing_key=GID + user_id, 
                body=msg,
                properties=pika.BasicProperties(delivery_mode=2)
            )
        else:
            msg = 'DELIVERY_FAILED ' + req_id
            print(f' [x] {msg}')
            channel.basic_publish(
                exchange='', 
                routing_key=D2X, 
                body=msg,
                properties=pika.BasicProperties(delivery_mode=2)
            )
                
        channel.basic_ack(delivery_tag=method.delivery_tag)

    def run(self):
        '''
        Ejecuta el bucle de escuha y procesamiento de mensajes hasta que se 
        recibe la interrupción de teclado.
        '''

        try:
            self.channel.start_consuming()
        except:
            self.channel.stop_consuming()
        
        self.connection.close()
