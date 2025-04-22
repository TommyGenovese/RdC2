import pika
import sys
import threading
import time

from consumer import Consumer
from client import C2X

class ControllerInterface(Consumer):
    def __init__(self, controller, queue:str) -> None:
        super().__init__(queue, self.__on_consume)
        self.controller = controller
    
    def __on_consume(self, channel, method, properties, body):
        msg_type = body.decode().split()[0]
        if msg_type == 'SIGNED_IN':
            with self.controller.lock:
                self.controller.signed_in = True
        elif msg_type == 'SIGNED_OUT':
            with self.controller.lock:
                self.controller.signed_in = False
        print(f'\r [<] {body.decode()}\n [>] ', end='')
        channel.basic_ack(delivery_tag=method.delivery_tag)

class TestClient:
    def __init__(self, user) -> None:
        self.user = user
        self.signed_in = False
        self.lock = threading.Lock()
        self.controllerInterface = ControllerInterface(self, self.user)
        self.listenerThread = threading.Thread(target=self.controllerInterface.run, name='ControllerInterface')

    def run(self):
        self.listenerThread.start()
        connection = pika.BlockingConnection(
            parameters=pika.ConnectionParameters(host='localhost')
        )
        channel = connection.channel()
        print(' [*] Comandos: sign_up, sign_in, sign_out, request, view, cancel')
        try:
            while True:
                tokens = input(' [>] ').strip().split()
                msg = f'{tokens[0].upper()} {self.user} {' '.join(tokens[1:])}'
                channel.basic_publish(
                    exchange='',
                    routing_key=C2X,
                    body=msg,
                    properties=pika.BasicProperties(delivery_mode=2)
                )
        except KeyboardInterrupt:
            print('')
            with self.lock:
                if self.signed_in:
                    channel.basic_publish(
                        exchange='',
                        routing_key=C2X,
                        body=f'SIGN_OUT {self.user}',
                        properties=pika.BasicProperties(delivery_mode=2)
                    )
            connection.close()
            self.controllerInterface.connection.ioloop.add_callback_threadsafe(
                callback=self.controllerInterface.stop
            )
            self.listenerThread.join()
            print(' [*] Saliendo...')

if len(sys.argv) < 2:
    print(' [x] Uso: controller_test.py <user_id>')
    exit()

cl = TestClient(sys.argv[1])
print(' [✓] Nuevo cliente iniciado.')
cl.run()
