'''
Implementación de las funciones de acceso y actualización de la base de datos.

Se utiliza el módulo sqlite3 de Python para conectarse (y crear) una base de
datos, añadir los clientes, pedidos y productos, y actualizar su estado,
almacenando en disco el estado del sistema tras cada transacción.

Clases
------
Database
    Clase que gestiona la conexión a la base de datos y su actualización.
'''

import sqlite3
import uuid
from pathlib import Path
from threading import Lock

import request
from state import ProductState, RequestState, ClientState

class Database:
    '''
    Clase que gestiona la conexión a la base de datos y su actualización.

    Parámetros
    ----------
    name : str
        Ruta de la base de datos.
    
    Atributos
    ---------
    path : pathlib.Path
        Ruta de la base de datos como instancia de Path.
    lock : threading.Lock
        Lock que regula el acceso de los hilos a la base de datos.
    connection : sqlite3.Connection
        Conexión con la base de datos.
    cursor : sqlite3.Cursor
        Cursor utilizado para realizar consultas y actualizar la base de datos.

    Métodos
    -------
    getClientState(user_id)
        Obtiene de la base de datos el estado del cliente identificado por 
        user_id.
    registerClient(user_id)
        Añade un cliente identificado por user_id a la base de datos.
    updateClient(user_id, state)
        Cambia el estado del cliente identificado por user_id a state.
    getRequest(id)
        Obtiene de la base de datos el pedido identificado por id.
    addRequest(req)
        Añade la información del pedido req a la base de datos.
    updateRequest(req_id, update, user_id, args)
        Actualiza el estado del pedido identificado por req_id según la función
        update.
    getClientRequests(user_id)
        Obtiene todos los pedidos realizados por el cliente identificado por
        user_id.
    close()
        Cierra la conexión con la base de datos.
    
    Excepciones
    -----------
    ValueError
        En caso de que la compilación de SQLite presente en la máquina no
        tenga habilitado el acceso multihilo seguro.
    '''

    def __init__(self, name:str) -> None:
        self.path = Path(name)
        self.lock = Lock()
        db_existed = self.path.is_file()
        if sqlite3.threadsafety != 3:
            raise ValueError('Necesario actualizar THREADSAFE=1 en la compilación de SQLite para permitir el acceso multihilo a la base de datos.')
        self.connection = sqlite3.connect(
            database=self.path,
            check_same_thread=False
        )
        self.cursor = self.connection.cursor()
        if not db_existed:
            self.__db_create()

    def __db_create(self):
        '''
        Inicializa la base de datos creando las tablas.

        Crea las siguientes tablas: clients, para el identificador y el estado 
        de los clientes; requests, para el estado y el cliente de cada pedido; y 
        request_products, para el nombre y estado de los productos de cada 
        pedido.
        '''

        self.cursor.execute("""
            CREATE TABLE clients(
                user_id TEXT NOT NULL UNIQUE,
                client_state INTEGER NOT NULL,
                PRIMARY KEY (user_id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE requests(
                req_id BLOB NOT NULL UNIQUE,
                user_id TEXT NOT NULL,
                req_state INTEGER NOT NULL,
                PRIMARY KEY (req_id),
                FOREIGN KEY (user_id) REFERENCES clients(user_id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE request_products(
                req_id BLOB NOT NULL,
                name TEXT NOT NULL,
                prod_state INTEGER NOT NULL,
                PRIMARY KEY (req_id, name),
                FOREIGN KEY (req_id) REFERENCES requests(req_id)
            )
        """)

    def getClientState(self, user_id:str):
        '''
        Obtiene de la base de datos el estado del cliente identificado por 
        user_id.

        Parámetros
        ----------
        user_id : str
            Identificador del usuario del que se obtiene el estado.
        
        Retorno
        -------
        getClientState : state.ClientState
            El estado almacenado en la base de datos para el cliente, o 
            ClientState.NOT_REGISTERED si no está en la base de datos.
        '''

        res = self.cursor.execute("""
            SELECT client_state
            FROM clients
            WHERE user_id = ?
        """, (user_id,))
        row = res.fetchone()
        if row is None:
            return ClientState.NOT_REGISTERED
        return ClientState(row[0])
    
    def registerClient(self, user_id:str):
        '''
        Añade un cliente identificado por user_id a la base de datos.

        Parámetros
        ----------
        user_id : str
            Identificador del usuario que se añade a la base de datos.
        
        Retorno
        -------
        registerClient : int
            -1 si el usuario ya existe; si no, el número de filas de la base de
            datos modificadas (1 si se añade la información correctamente).
        '''

        with self.lock:
            if self.getClientState(user_id) != ClientState.NOT_REGISTERED:
                return -1
            self.cursor.execute("""
                INSERT INTO clients
                VALUES (?, ?)
            """, (user_id, ClientState.SIGNED_OUT.value))
            self.connection.commit()
            return self.cursor.rowcount

    def updateClient(self, user_id:str, state:ClientState):
        '''
        Cambia el estado del cliente identificado por user_id a state.

        Parámetros
        ----------
        user_id : str
            Identificador del usuario cuyo estado se va a modificar.
        state : state.ClientState
            El nuevo estado del usuario.

        Retorno
        -------
        updateClient : int
            -1 si el cliente no está registrado o el nuevo estado no es válido;
            en caso contrario, el número de filas de la base de datos 
            modificadas (1 si se añade la información correctamente).
        '''

        with self.lock:
            cs = self.getClientState(user_id)
            if cs == ClientState.NOT_REGISTERED or cs == state or state == ClientState.NOT_REGISTERED:
                return -1
            self.cursor.execute("""
                UPDATE clients
                SET client_state = ?
                WHERE user_id = ?
            """, (state.value, user_id))
            self.connection.commit()
            return self.cursor.rowcount

    def __getRequest(self, id:uuid.UUID):
        '''
        Este método no es seguro en entornos multihilo y es solo para uso dentro
        de esta clase. Utilizar getRequest en su lugar.
        '''

        res = self.cursor.execute("""
            SELECT user_id, req_state
            FROM requests
            WHERE req_id = ?
        """, (id.bytes,))
        row = res.fetchone()
        if row is None:
            return None
        
        user_id = row[0]
        state = RequestState(row[1])
        res = self.cursor.execute("""
            SELECT name, prod_state
            FROM request_products
            WHERE req_id = ?
        """, (id.bytes,))
        products = [request.Product.productFromDB(row[0], ProductState(row[1])) for row in res]
        
        return request.Request.requestFromDB(user_id, products, id, state)
  
    def getRequest(self, id:uuid.UUID):
        '''
        Obtiene de la base de datos el pedido identificado por id.

        Parámetros
        ----------
        id : uuid.UUID
            Id del pedido a obtener.
        
        Retorno
        -------
        getRequest : request.Request o None
            El pedido obtenido como instancia de Request, o None si el pedido
            no está en la base de datos.
        '''

        with self.lock:
            return self.__getRequest(id)

    def addRequest(self, req:request.Request):
        '''
        Añade la información del pedido req a la base de datos.

        Parámetros
        ----------
        req : request.Request
            El objeto con la información el pedido que se quiere añadir

        Retorno
        -------
        addRequest : int
            -1 si ya existe un pedido con la misma id o si el cliente que hace
            el pedido no ha iniciado sesión; en caso contrario, el número de 
            filas de la tabla requests que se han modificado (1 si se añade la
            información correctamente).
        '''

        with self.lock:
            if self.__getRequest(req.getId()) is not None:
                print(f' [x] Ya existe un pedido con id {req.getId()}.')
                return -1
            if self.getClientState(req.getClient()) != ClientState.SIGNED_IN:
                print(f' [x] El usuario {req.getClient()} no ha iniciado sesión.')
                return -1
            
            self.cursor.execute("""
                INSERT INTO requests 
                VALUES (?, ?, ?)
            """, (req.getId().bytes, req.getClient(), req.getState().value))
            ret = self.cursor.rowcount
            prods = [(req.getId().bytes, p.getName(), p.getState().value) for p in req.getProducts()]
            self.cursor.executemany("""
                INSERT INTO request_products
                VALUES (?, ?, ?)
            """, prods)
            
            self.connection.commit()
            return ret

    def updateRequest(self, req_id:uuid.UUID, update, user_id:str | None = None, args=()):
        '''
        Actualiza el estado del pedido identificado por req_id según la función
        update.

        La función update debe recibir un objeto de la clase Request y una tupla
        con el resto de argumentos, y devolver el objeto de clase Product que se
        haya modificado si lo hay; si no, debe retornar None.

        Con cada transacción de este tipo se podrá modificar, por lo tanto, un 
        producto del pedido como máximo.

        Opcionalmente se puede introducir el identificador del cliente que 
        solicita el cambio, si lo hay, como ocurre durante la cancelación de
        productos, para comprobar que coincide con el que realizó el pedido.

        Parámetros
        ----------
        req_id : uuid.UUID
            La id del pedido a actualizar.
        update : callable
            Función que recibe un pedido en forma de instancia de Request y unos
            argumentos en forma de tuple, y actualiza el estado del pedido.
        user_id : str o None, opcional
            Id del cliente que solicita el cambio.
        args : tuple, opcional
            Argumentos requeridos por la función update.
        
        Retorno
        -------
        updateRequest : request.Request
            El pedido resultante tras la actualización, o None en caso de que el
            pedido no exista o el cliente que pide la actualización no coincida
            con el que realizó el pedido.
        '''

        with self.lock:
            req = self.__getRequest(req_id) # get the Request instance
            if req is None:
                print(f' [x] No existe un pedido con id {req_id}.')
                return None
            if user_id is not None and (req.getClient() != user_id or self.getClientState(user_id) != ClientState.SIGNED_IN):
                print(f' [x] El usuario no coincide con el que realizó el pedido.')
                return None
            
            p_modified = update(req, args) # update the Request instance and get
                                           # the modified product if there was one

            self.cursor.execute("""
                UPDATE requests
                SET req_state = ?
                WHERE req_id = ?
            """, (req.getState().value, req_id.bytes))
            if p_modified is not None:
                self.cursor.execute("""
                    UPDATE request_products
                    SET prod_state = ?
                    WHERE req_id = ? AND name = ?
                """, (p_modified.getState().value, req_id.bytes, p_modified.getName()))
            
            self.connection.commit()
            return req
        
    def getClientRequests(self, user_id:str):
        '''
        Obtiene todos los pedidos realizados por el cliente identificado por
        user_id.

        Parámetros
        ----------
        user_id : str
            El identificador del usuario cuyos pedidos se van a obtener.
        
        Retorno
        -------
        getClientRequests : list[request.Request]
            Lista de todos los pedidos que ha realizado el usuario.
        '''

        with self.lock:
            res = self.cursor.execute("""
                SELECT req_id
                FROM requests NATURAL JOIN clients
                WHERE user_id = ?
            """, (user_id,))
            return [self.__getRequest(uuid.UUID(bytes=row[0])) for row in res.fetchall()]
    
    def close(self):
        '''
        Cierra la conexión con la base de datos.

        Según la documentación de sqlite3, esta operación hace un rollback, 
        descartando las transacciones que queden pendientes. Esto no debería
        suponer un problema en este caso, ya que cada método que modifica la
        base de datos realiza un commit (confirmación de las transacciones), 
        y el lock impide que se cierre la conexión mientras otro hilo está
        realizando una transacción.

        Aun así, se debe llamar a esta funcióm tras recoger los hilos, para
        evitar que intenten modificar la base de datos tras cerrar la conexión.
        '''

        with self.lock:
            self.connection.close()