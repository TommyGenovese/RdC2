'''
Implementación del robot que busca los productos.

El éxito o fallo al buscar el producto se simula realizando una espera aleatoria
de entre 5 y 10 segundos, y después generando un número aleatorio entre 0 y 1
mediante el módulo random. Si este número es inferior a la probabilidad de
encontrar el producto definida en la clase Robot, se determina que el intento ha
sido exitoso.

Clases
------
Robot
    Clase usada para representar al robot y realizar sus funciones.
'''

import pika
import time
import random

from config import HOST, X2R, R2X

class Robot:
    '''
    Clase usada para representar al robot y realizar sus funciones.

    Atributos
    ---------
    p_producto : float
        Probabilidad de que se encuentre el producto.
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

    p_producto = 0.8
    '''Probabilidad de que se encuentre el producto.'''

    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=HOST))
        self.channel = self.connection.channel()

        self.channel.queue_declare(X2R, durable=True)
        self.channel.queue_declare(R2X, durable=True)
        
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue=X2R, on_message_callback=self.__on_consume)
    
    def __on_consume(self, ch, method, properties, body):
        '''
        Función de callback para consumir los mensajes del controlador.

        Tokeniza el mensaje recibido y analiza el valor del primer token, que 
        solo puede ser 'MOVE'.
        
        Si lo es, simula la búsqueda del producto en el almacén e informa al
        controlador del resultado.

        Si no, el mensaje se descarta.
        '''
        
        message = body.decode().split()  # Dividimo el mensaje en una lista de palabras

        if message[0] != 'MOVE':
            print(f' [x] Mensaje no válido recibido: {body.decode()}')
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        if len(message) < 3:  # Minimo req_id + 1 producto
            print(f' [x] Mensaje no válido recibido: {body.decode()}')
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        queue_destino = R2X
        req_id = message[1]  # ID del pedido
        producto = message[2]  # Lista de productos

        tiempo_trabajo = random.randint(5, 10)

        # Simulamos el tiempo de trabajo (moviendo el producto)
        tiempo_trabajo = random.randint(5, 10)
        print(f' [*] Buscando \'{producto}\' ({tiempo_trabajo} seg)')
        time.sleep(tiempo_trabajo)

        # Decidimos si el producto fue encontrado o no
        # En este caso, el 80% de las veces el producto es encontrado
        if random.random() < Robot.p_producto:
            respuesta = f'MOVED {req_id} {producto}'
            print(f' [✓] {respuesta}')
        else:
            respuesta = f'NOT_FOUND {req_id} {producto}'
            print(f' [x] {respuesta}')

        # Enviamos la respuesta a la cola correspondiente por CADA producto
        ch.basic_publish(
            exchange='',
            routing_key=queue_destino,
            body=respuesta,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Hace el mensaje persistente
            )
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
    
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