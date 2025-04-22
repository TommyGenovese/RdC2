'''
Configuración del host de las colas de mensajes y el nombre de las colas.

Constantes
----------
DB : str
    Nombre de la base de datos.
HOST : str
    Nombre del host de las colas.
GID : str
    Identificador de la pareja que ha realizado este proyecto.
C2X : str
    Nombre de la cola de mensajes del cliente (C) al controlador (X).
X2R : str
    Nombre de la cola de mensajes del controlador (X) al robot (R).
R2X : str
    Nombre de la cola de mensajes del robot (R) al controlador (X).
X2D : str
    Nombre de la cola de mensajes del controlador (X) al repartidor (D).
D2X : str
    Nombre de la cola de mensajes del repartidor (D) al controlador (X).
'''
DB = 'saimazoom.db'
'''Nombre de la base de datos.'''

HOST = 'localhost'
'''Nombre del host de las colas.'''

GID = '2312-09_'
'''Identificador de la pareja que ha realizado este proyecto.'''

C2X = GID + 'client_to_x'
'''Nombre de la cola de mensajes del cliente (C) al controlador (X).'''

X2R = GID + 'x_to_robot'
'''Nombre de la cola de mensajes del controlador (X) al robot (R).'''

R2X = GID + 'robot_to_x'
'''Nombre de la cola de mensajes del robot (R) al controlador (X).'''

X2D = GID + 'x_to_delivery'
'''Nombre de la cola de mensajes del controlador (X) al repartidor (D).'''

D2X = GID + 'delivery_to_x'
'''Nombre de la cola de mensajes del repartidor (D) al controlador (X).'''

