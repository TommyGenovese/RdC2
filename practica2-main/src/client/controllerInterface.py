'''
Implementación de las funciones que procesan los mensajes del controlador al
cliente.

Clases
------
ControllerInterface
    Clase que actúa como consumidor asíncrono de la cola por la que el cliente
    recibe mensajes.
'''

from state import ClientState
from consumer import Consumer

class ControllerInterface(Consumer):
    '''
    Clase que actúa como consumidor asíncrono de la cola por la que el cliente
    recibe mensajes.

    Extiende a la clase consumer.Consumer implementando el método de 
    procesamiento de los mensajes que el cliente recibe.

    Parámetros
    ----------
    queue : str
        Nombre de la cola por la que se reciben los mensajes.
    client : Client
        El cliente propietario de esta interfaz, es decir, el que la crea e 
        inicia y detiene su ejecución.

    Atributos
    ---------
    client : Client
        Referencia al parámetro client.
    '''

    def __init__(self, queue: str, client) -> None:
        super().__init__(queue, self.__on_consume)
        self.client = client
    
    def __on_consume(self, ch, method, props, body):
        '''
        Función de callback para consumir los mensajes que recibe el cliente.
        '''
        
        response = body.decode()

        # Si el mensaje contiene un indicador de éxito o fallo, lo procesamos
        if response.startswith('SIGNED_UP'):
            with self.client.lock:
                self.client.state = ClientState.SIGNED_OUT
            output = f'[✓] El usuario ha sido registrado exitosamente.'
        elif response.startswith('SIGNED_IN'):
            with self.client.lock:
                self.client.state = ClientState.SIGNED_IN
            output = f'[✓] Inicio de sesión exitoso.'
        elif response.startswith('SIGNED_OUT'):
            with self.client.lock:
                self.client.state = ClientState.SIGNED_OUT
            output = f'[✓] Cierre de sesión exitoso.'
        elif response.startswith('REQUEST_CREATED'):
            output = f'[✓] El pedido con id {response.split()[1]} se ha creado exitosamente.'
        elif response.startswith('CANCELLED'):
            output = f'[✓] El pedido con id {response.split()[1]} ha sido cancelado.'
        elif response.startswith('FOUND_REQUESTS'):
            output = f'[✓] Se ha(n) encontrado {response.count('\n')} pedido(s):{response.partition(' ')[2]}'
        elif response.startswith('RECEIVE'):
            output = f'[<] Pedido recibido:\n{response.partition(' ')[2]}'
        elif response.startswith('SIGN_UP_FAILED'):
            output = f'[x] El registro ha fallado. El usuario ya existe.'
        elif response.startswith('SIGN_IN_FAILED'):
            output = f'[x] El inicio de sesión ha fallado. El usuario no está registrado.'
        elif response.startswith('SIGN_OUT_FAILED'):
            output = f'[x] El cierre de sesión ha fallado. El usuario no ha iniciado sesión.'
        elif response.startswith('REQUEST_FAILED'):
            if len(response.split()) == 1:
                output = f'[x] No se pudo crear el pedido.'
            else:
                output = f'[x] No se pudo completar el pedido {response.split()[1]}.'
        elif response.startswith('CANCEL_FAILED'):
            output = f'[x] No se pudo cancelar el pedido {response.split()[1]}.'
        elif response.startswith('VIEW_FAILED'):
            output = f'[x] No se pudieron obtener los pedidos.'
        else:
            output = f'[x] Respuesta desconocida: {response}'
        
        if self.client.cmd_line:
            print(f'\r {output}\n [>] ', end='')
        else:
            print(f' {output}')
        
        ch.basic_ack(delivery_tag=method.delivery_tag)