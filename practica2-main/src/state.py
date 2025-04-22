'''
Definición de estados de diferentes elementos del sistema.

Clases
------
State
    Define una clase común para las enumeraciones de estados.
RequestState
    Define estados de un pedido.
ProductState
    Define estados de un producto.
ClientState
    Define estados de un cliente.
'''

from enum import Enum

class State(Enum):
    '''
    Define una clase común para las enumeraciones de estados.
    '''

    def __str__(self) -> str:
        return super().__str__().split('.')[1]

class RequestState(State):
    '''
    Define estados de un pedido.

    Las siguientes transiciones son posibles

    * IN_STORAGE  --> FAILED, CANCELLED, IN_CONVEYOR
    * IN_CONVEYOR --> FAILED, DELIVERED

    IN_STORAGE e IN_CONVEYOR son estados temporales, y FAILED, CANCELLED y 
    DELIVERED son estados finales.

    Miembros
    --------
    FAILED
        Pedido cuya entrega no se ha podido realizar por fallo del sistema.
    CANCELLED
        Pedido cancelado por el cliente que lo realizó.
    IN_STORAGE
        Pedido en almacén, es el estado inicial de un pedido.
    IN_CONVEYOR
        Pedido con productos empaquetados y a la espera de ser entregado.
    DELIVERED
        Pedido entregado con éxito
    '''

    FAILED = -2
    CANCELLED = -1
    IN_STORAGE = 0
    IN_CONVEYOR = 1
    DELIVERED = 2

class ProductState(State):
    '''
    Define estados de un producto.

    Las siguientes transiciones son posibles

    * UNDEFINED --> NOT_FOUND, FOUND

    UNDEFINED es un estado temporal, y NOT_FOUND y FOUND son estados finales.

    Miembros
    --------
    UNDEFINED
        Estado inicial de un producto, no se ha buscado todavía.
    NOT_FOUND
        El producto no se ha encontrado.
    FOUND
        El producto se ha encontrado
    '''

    UNDEFINED = -1
    NOT_FOUND = 0
    FOUND = 1

class ClientState(State):
    '''
    Las siguientes transiciones son posibles

    * NOT_REGISTERED --> SIGNED_OUT
    * SIGNED_OUT     --> SIGNED_IN
    * SIGNED_IN      --> SIGNED_OUT

    Miembros
    --------
    NOT_REGISTERED
        Cliente no registrado en la base de datos.
    SIGNED_OUT
        Cliente registrado con la sesión cerrada.
    SIGNED_IN
        Cliente registrado con la sesión iniciada.
    '''

    NOT_REGISTERED = -1
    SIGNED_OUT = 0
    SIGNED_IN = 1