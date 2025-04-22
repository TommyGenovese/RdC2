import sys
import signal

from client import Client
from state import ClientState

def signal_handler(signum, stack_frame):
    '''
    Función de manejo de la señal SIGINT.

    Indica al usuario la forma correcta de cerrar la apliación.
    '''

    print(f'\r [*] Para salir, use el comando exit.\n [>] ', end='')

if len(sys.argv) < 2:
    print(' [x] Uso: launch_client.py <user_id>')
    exit()

sigset = signal.valid_signals()
sigset.remove(signal.SIGINT)
signal.pthread_sigmask(signal.SIG_BLOCK, sigset)
signal.signal(signal.SIGINT, signal_handler)

client = Client(sys.argv[1], cmd_line=True)
print(f' [✓] Conectado como {sys.argv[1]}.')
print(' [*] Comandos: sign_up | sign_in | sign_out | request <p1> [p2 ...] | view | cancel <req_id> | help | exit')
while True:
    try:
        command = input(' [>] ').strip().split()
    except EOFError:
        print('\r', end='')
        continue
    if len(command) < 1:
        continue
    action = command[0]

    if action == 'sign_up':
        with client.lock:
            if client.state != ClientState.NOT_REGISTERED:
                print(' [x] Ya te has registrado.')
                continue
        client.sign_up()
    elif action == 'sign_in':
        with client.lock:
            if client.state == ClientState.SIGNED_IN:
                print(' [x] Ya has iniciado sesión.')
                continue
        client.sign_in()
    elif action in ['request', 'view', 'cancel', 'sign_out']:
        with client.lock:
            if client.state != ClientState.SIGNED_IN:
                print(' [x] Tienes que iniciar sesión primero.')
                continue

        if action == 'request':
            if len(command) < 2:
                print(' [x] Uso correcto: request <p1> [p2 ...]')
                continue    
            client.request(command[1:])
        elif action == 'view':
            client.view()
        elif action == 'sign_out':
            client.sign_out()
        elif action == 'cancel' and len(command) == 2:
            client.cancel(command[1])
        else:
            print(' [x] Uso correcto: cancel <req_id>')

    elif action == 'help':
        print(' [*] Comandos: sign_up | sign_in | sign_out | request p1 p2 ... | view | cancel <req_id> | help | exit')
    elif action == 'exit':
        with client.lock:
            if client.state == ClientState.SIGNED_IN:
                print(' [x] Cierre la sesión antes de salir.')
                continue
        print(' [*] Saliendo...')
        break
    else:
        print(' [x] Comando inválido.')

client.stop()