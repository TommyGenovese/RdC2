'''
Implementación de las funciones comunes de recepción de mensajes en una
aplicación multihilos.

Clases
------
Consumer
    Clase usada para representar a un consumidor asíncrono genérico de una cola 
    de mensajes que trabaja en un entorno multihilo.
'''

import pika

from config import HOST

class Consumer:
    '''
    Clase usada para representar a un consumidor asíncrono genérico de una cola 
    de mensajes que trabaja en un entorno multihilo.

    Parámetros
    ----------
    queue : str
        Nombre de la cola cuyos mensajes consume la interfaz.
    on_consume : callable
        Función de callback usada para el procesamiento de los mensajes 
        recibidos, siguiendo el formato requerido por el método basic_consume 
        del módulo pika.
    
    Atributos
    ---------
    queue : str
        Referencia al parámetro queue.
    on_consume : callable
        Referencia al parámetro consumer.
    connection : pika.SelectConnection
        Conexión con RabbitMQ.
    channel : pika.channel.Channel
        Canal de comunicación con RabbitMQ obtenido de connection.

    Métodos
    -------
    run()
        Ejecuta el bucle de procesamiento de mensajes.
    stop()
        Detiene el bucle de procesamiento de mensajes.
    '''

    def __init__(self, queue:str, on_consume) -> None:
        self.queue = queue
        self.on_consume = on_consume
        self.connection = pika.SelectConnection(
            parameters=pika.ConnectionParameters(host=HOST),
            on_open_callback=self.__on_connection_open,
            on_close_callback=self.__on_connection_close
        )
    
    def __on_connection_open(self, conn):
        '''
        Función de callback que se utiliza al abrir la conexión.

        Guarda la conexión y abre un canal.
        '''

        self.connection = conn
        self.connection.channel(on_open_callback=self.__on_channel_open)
        
    def __on_connection_close(self, conn, exception):
        '''
        Función de callback que se utiliza al cerrar la conexión.

        Detiene el bucle de procesamiento de mensajes.
        '''

        conn.ioloop.stop()

    def __on_channel_open(self, ch):
        '''
        Función de callback que se utiliza al abrir el canal.

        Guarda el canal y declara la cola de escucha.
        '''

        self.channel = ch
        self.channel.queue_declare(queue=self.queue, durable=True, callback=self.__on_queue_declare)
    
    def __on_queue_declare(self, frame):
        '''
        Función de callback que se utiliza al declarar la cola.

        Añade el callback de consumo de mensajes.
        '''

        self.channel.basic_consume(queue=self.queue, on_message_callback=self.on_consume)

    def run(self):
        '''
        Ejecuta el bucle de procesamiento de mensajes.
        '''
        
        try:
            self.connection.ioloop.start()
        except:
            self.connection.close()
            self.connection.ioloop.start()
        
        print(f' [*] Cerrando {self.__class__.__name__}.')
    
    def stop(self):
        '''
        Detiene el bucle de procesamiento de mensajes.

        Para usar este método, debe utilizarse desde otro hilo la función 
        add_callback_threadsafe() proporcionada por la propiedas ioloop de 
        la conexión con este método como argumento.
        '''

        self.connection.ioloop.stop()
        self.connection.close()