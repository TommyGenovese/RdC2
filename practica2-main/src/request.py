'''
Implementación de los pedidos y los productos que contienen.

Clases
------
Product
    Clase usada para representar un producto de un pedido.
Request
    Clase usada para representar un pedido.

Funciones
---------
productsFromString(string)
    Genera una lista de productos con nombres obtenidos de string.
on_cancel(req, args)
    Decorador de Request.cancel para usarlo como argumento del método 
    updateRequest de la clase Database.
on_moved(req, args)
    Decorador de Request.found y Request.move para usarlo como argumento del 
    método updateRequest de la clase Database.
on_notFound(req, args)
    Decorador de Request.notFound para usarlo como argumento del método 
    updateRequest de la clase Database.
on_deliver(req, args)
    Decorador de Request.deliver para usarlo como argumento del método 
    updateRequest de la clase Database.
on_fail(req, args)
    Decorador de Request.fail para usarlo como argumento del método 
    updateRequest de la clase Database.
'''

import uuid

from state import ProductState
from state import RequestState

    
class Product:
    '''
    Clase usada para representar un producto de un pedido.

    El producto tiene un nombre y un estado, que inicialmente es UNDEFINED.
    Este estado se puede cambiar a FOUND o NOT_FOUND.

    Parámetros
    ----------
    name : str
        Nombre del producto, sirve como su identificador dentro del pedido.
    
    Atributos
    ---------
    __name : str
        Atributo en el que se almacena el parámetro name.
    __state : state.ProductState
        El estado en el que se encuentra el producto.
    
    Métodos
    -------
    getName()
        Retorna el nombre del producto.
    getState()
        Retorna el estado del producto.
    found()
        Cambia el estado del producto a FOUND.
    notFound()
        Cambia el estado del producto a NOT_FOUND.
    productFromDB(name, state) : staticmethod
        Genera un producto con un nombre y un estado pasados como argumentos.
    '''

    def __init__(self, name:str) -> None:
        self.__name = name
        self.__state = ProductState.UNDEFINED

    def __str__(self) -> str:
        return self.__name + ' ' + str(self.__state)
    
    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, Product):
            return self.__name == __value.__name and self.__state == __value.__state
        return False
    
    def getName(self):
        '''
        Retorna el nombre del producto.
        '''
        return self.__name
    
    def getState(self):
        '''
        Retorna el estado del producto.
        '''
        return self.__state
    
    def found(self):
        '''
        Cambia el estado del producto a FOUND.

        El cambio solo se realiza si el estado previo es UNDEFINED, es decir,
        no se puede realizar una transición de NOT_FOUND a FOUND.

        Retorno
        -------
        found : state.ProductState
            El estado final del producto.
        '''

        if self.__state == ProductState.UNDEFINED:
            self.__state = ProductState.FOUND
        return self.__state
    
    def notFound(self):
        '''
        Cambia el estado del producto a NOT_FOUND.

        El cambio solo se realiza si el estado previo es UNDEFINED, es decir,
        no se puede realizar una transición de FOUND a NOT_FOUND.

        Retorno
        -------
        found : state.ProductState
            El estado final del producto.
        '''

        if self.__state == ProductState.UNDEFINED:
            self.__state = ProductState.NOT_FOUND
        return self.__state
    
    @staticmethod
    def productFromDB(name:str, state:ProductState):
        '''
        Genera un producto con un nombre y un estado pasados como argumentos.

        Esta función se utiliza para generar un producto a partir de información
        obtenida de una base de datos, que puede almacenar productos en estados 
        distintos al UNDEFINED inicial.

        Parámetros
        ----------
        name : str
            El nombre del producto.
        state : state.ProductState
            El estado del producto.
        
        Retorno
        -------
        productFromDB : Product
            Un nuevo objeto de clase Product con el nombre y estado dados.
        '''
        p = Product(name)
        p.__state = state
        return p

class Request:
    '''
    Clase usada para representar un pedido.

    El pedido tiene un identificador único generado mediante el módulo uuid, un 
    cliente, una lista de productos (Product) y un estado (RequestState).

    Parámetros
    ----------
    client : str
        El identificador del cliente que realiza el pedido.
    products : list[Product]
        La lista de productos del pedido
    
    Atributos
    ---------
    __id : uuid.UUID
        Identificador único del pedido generado al azar.
    __client : str
        Atributo en el que se almacena el parámetro client.
    __products : list[Product]
        Atributo en el que se almacena el parámetro products.
    __state : state.RequestState
        Estado del pedido.
    
    Métodos
    -------
    requestInfo()
        Devuelve una cadena con el cliente, el identificador y el nombre de cada
        producto del pedido.
    getClient()
        Retorna el nombre del cliente que realiza el pedido.
    getId()
        Retorna el identificador del pedido.
    getProducts()
        Retorna la lista de productos del pedido.
    getState()
        Retorna el estado del pedido.
    stateIsTemporary()
        Indica si el pedido está en un estado temporal, no final.
    cancel()
        Cambia el estado del pedido a CANCELLED.
    found(product)
        Cambia el estado de product a FOUND dentro de la lista de productos del
        pedido.
    notFound(product)
        Cambia el estado de product a NOT_FOUND dentro de la lista de productos 
        del pedido, y el estado del pedido a FAILED.
    areProductsPacked()
        Indica si se han encontrado todos los productos del pedido.
    move()
        Cambia el estado del pedido a IN_CONVEYOR.
    deliver()
        Cambia el estado del pedido a DELIVERED.
    fail()
        Cambia el estado del pedido a FAILED.
    requestFromDB(client, products, id, state) : staticmethod
        Genera un pedido con cliente, productos, identificador y estado pasados 
        como argumentos.
    '''

    def __init__(self, client:str, products:list[Product]) -> None:
        self.__id = uuid.uuid4()
        self.__client = client
        self.__products = products
        self.__state = RequestState.IN_STORAGE

    def __str__(self) -> str:
        return self.requestInfo() + ' ' + str(self.__state)
    
    def requestInfo(self) -> str:
        '''
        Devuelve una cadena con el cliente, el identificador y el nombre de cada
        producto del pedido.
        '''

        ret = self.__client + ' ' + str(self.__id)
        for product in self.__products:
            ret += ' ' + product.getName()
        return ret
    
    def getClient(self):
        '''
        Retorna el nombre del cliente que realiza el pedido.
        '''
        return self.__client
    
    def getId(self):
        '''
        Retorna el identificador del pedido.
        '''
        return self.__id
    
    def getProducts(self):
        '''
        Retorna la lista de productos del pedido.
        '''
        return self.__products
    
    def getState(self):
        '''
        Retorna el estado del pedido.
        '''
        return self.__state
    
    def stateIsTemporary(self):
        '''
        Indica si el pedido está en un estado temporal, no final.

        Retorno
        -------
        stateIsTemporary : bool
            True, si el estado es IN_STORAGE o IN_CONVEYOR; False en 
            caso contrario.
        '''

        return self.__state == RequestState.IN_STORAGE or self.__state == RequestState.IN_CONVEYOR
    
    def cancel(self):
        '''
        Cambia el estado del pedido a CANCELLED.

        El cambio solo se realiza si el producto está en estado IN_STORAGE, es
        decir, todavía en el almacén.

        Retorno
        -------
        cancel : state.RequestState
            El estado final del pedido.
        '''
        
        if self.__state == RequestState.IN_STORAGE:
            self.__state = RequestState.CANCELLED
        return self.__state
    
    def found(self, product:Product):
        '''
        Cambia el estado de product a FOUND dentro de la lista de productos del
        pedido.

        Busca en la lista de productos del pedido uno que tenga el mismo nombre
        que product, y, si lo encuentra, llama a su método found(), de modo que
        solo cambia su estado a FOUND si es posible.

        Este método no modifica la instancia de Product introducida como
        parámetro.

        Parámetros
        ----------
        product : Product
            Un producto con el mismo nombre que el producto que se quiere
            cambiar dentro del pedido.
        
        Retorno
        -------
        found : Product o None
            Si se realiza el cambio de estado, retorna el producto modificado, 
            es decir, la instancia de Product de la lista del pedido que se ha 
            cambiado; si no, retorna None.
        '''

        if self.__state != RequestState.IN_STORAGE:
            return None
        for p in self.__products:
            if p.getName() == product.getName():
                if p.found() == ProductState.FOUND:
                    return p
                return None
        return None
    
    def notFound(self, product:Product):
        '''
        Cambia el estado de product a NOT_FOUND dentro de la lista de productos 
        del pedido, y el estado del pedido a FAILED.

        Busca en la lista de productos del pedido uno que tenga el mismo nombre
        que product, y, si lo encuentra, llama a su método notFound(), de modo 
        que solo cambia su estado a NOT_FOUND si es posible. Si esto ocurre, 
        cambia el estado del pedido a FAILED.

        Este método no modifica la instancia de Product introducida como
        parámetro.

        Parámetros
        ----------
        product : Product
            Un producto con el mismo nombre que el producto que se quiere
            cambiar dentro del pedido.
        
        Retorno
        -------
        notFound : Product o None
            Si se realiza el cambio de estado, retorna el producto modificado, 
            es decir, la instancia de Product de la lista del pedido que se ha 
            cambiado; si no, retorna None.
        '''

        if self.__state != RequestState.IN_STORAGE:
            return None
        for p in self.__products:
            if p.getName() == product.getName():
                if p.notFound() == ProductState.NOT_FOUND:
                    self.__state = RequestState.FAILED
                    return p
                return None
        return None
    
    def areProductsPacked(self):
        '''
        Indica si se han encontrado todos los productos del pedido.

        Retorno
        -------
        areProductsPacked : bool
            True, si todos los productos de la lista están en estado FOUND;
            False en caso contrario.
        '''

        for product in self.__products:
            if product.getState() != ProductState.FOUND:
                return False
        return True
    
    def move(self):
        '''
        Cambia el estado del pedido a IN_CONVEYOR.

        El cambio solo se realiza si el producto está en estado IN_STORAGE, es
        decir, todavía en el almacén, y todos los productos están en estado
        FOUND.
        
        Retorno
        -------
        move : state.RequestState
            El estado final del pedido.
        '''

        if self.__state == RequestState.IN_STORAGE and self.areProductsPacked():
            self.__state = RequestState.IN_CONVEYOR
        return self.__state

    def deliver(self):
        '''
        Cambia el estado del pedido a DELIVERED.

        El cambio solo se realiza si el producto está en estado IN_CONVEYOR, es
        decir, esperando para ser entregado.

        Retorno
        -------
        deliver : state.RequestState
            El estado final del pedido.
        '''

        if self.__state == RequestState.IN_CONVEYOR:
            self.__state = RequestState.DELIVERED
        return self.__state
    
    def fail(self):
        '''
        Cambia el estado del pedido a FAILED.

        El cambio solo se realiza si el producto está en un estado temporal, es
        decir, IN_STORAGE o IN_CONVEYOR.

        Retorno
        -------
        fail : state.RequestState
            El estado final del pedido.
        '''

        if self.stateIsTemporary():
            self.__state = RequestState.FAILED
        return self.__state
    
    @staticmethod
    def requestFromDB(client:str, products:list[Product], id:uuid.UUID, state:RequestState):
        '''
        Genera un pedido con cliente, productos, identificador y estado pasados 
        como argumentos.

        Esta función se utiliza para generar un pedido a partir de información
        obtenida de una base de datos, que puede almacenar pedidos en estados 
        distintos al IN_STORAGE inicial, con identificadores específicos y
        productos en diversos estados.

        Parámetros
        ----------
        client : str
            El cliente que realizó el pedido.
        products : list[Product]
            Lista de productos del pedido.
        id : uuid.UUID
            Identificador del pedido.
        state : state.RequestState
            El estado del pedido.
        
        Retorno
        -------
        requestFromDB : Request
            Un nuevo objeto de clase Request con el cliente, los productos, el
            identificador y el estado dados.
        '''

        req = Request(client, products)
        req.__id = id
        req.__state = state
        return req

def productsFromString(string:str) -> list[Product]:
    '''
    Genera una lista de productos con nombres obtenidos de string.

    Parámetros
    ----------
    string : str
        Una cadena con los nombres de los productos separados por espacios.
    
    Retorno
    -------
    productsFromString : list[Product]
        Una lista de Productos en estado UNDEFINED con los nombres obtenidos de
        la cadena.
    '''

    return [Product(p) for p in string.split()]

def on_cancel(req:Request, args):
    '''
    Decorador de Request.cancel para usarlo como argumento del método 
    updateRequest de la clase Database.

    Llama al método cancel del pedido dado.

    Parámetros
    ----------
    req : Request
        Instancia de Request sobre la que se llama a cancel.
    args : tuple
        Requerido por el formato de decorador, no se utiliza.
    
    Retorno
    -------
    on_cancel : None
        Requerido por el formato de decorador, se devuelve None porque no se 
        modifica ningún producto.
    '''

    req.cancel()
    return None

def on_moved(req:Request, args):
    '''
    Decorador de Request.found y Request.move para usarlo como argumento del 
    método updateRequest de la clase Database.

    Si el pedido no está en un estado temporal, no se va a cambiar su estado, y 
    se devuelve None para evitar buscar en la lista de productos, que puede ser 
    costoso.

    En caso contrario, llama al método found del pedido dado e intenta moverlo a 
    estado IN_CONVEYOR llamando a move. El retorno es el del método found.

    Parámetros
    ----------
    req : Request
        Instancia de Request sobre la que se llama a found y move.
    args : tuple
        Tupla cuyo primer elemento es el producto que se pasará a found.
    
    Retorno
    -------
    on_moved : Product o None
        El producto modificado, si lo hay; None si no se modifica el producto.
    '''

    if not req.stateIsTemporary():
        return None
    p = req.found(args[0])
    req.move()
    return p

def on_notFound(req:Request, args):
    '''
    Decorador de Request.notFound para usarlo como argumento del método 
    updateRequest de la clase Database.

    Si el pedido no está en un estado temporal, no se va a cambiar su estado, y 
    se devuelve None para evitar buscar en la lista de productos, que puede ser 
    costoso.

    En caso contrario, llama al método notFound del pedido dado y devuelve su
    retorno.

    Parámetros
    ----------
    req : Request
        Instancia de Request sobre la que se llama a found y move.
    args : tuple
        Tupla cuyo primer elemento es el producto que se pasará a notFound.
    
    Retorno
    -------
    on_moved : Product o None
        El producto modificado, si lo hay; None si no se modifica el producto.
    '''
    if not req.stateIsTemporary():
        return None
    return req.notFound(args[0])
    
def on_deliver(req:Request, args):
    '''
    Decorador de Request.deliver para usarlo como argumento del método 
    updateRequest de la clase Database.

    Llama al método deliver del pedido dado.

    Parámetros
    ----------
    req : Request
        Instancia de Request sobre la que se llama a deliver.
    args : tuple
        Requerido por el formato de decorador, no se utiliza.
    
    Retorno
    -------
    on_deliver : None
        Requerido por el formato de decorador, se devuelve None porque no se 
        modifica ningún producto.
    '''

    req.deliver()
    return None

def on_fail(req:Request, args):
    '''
    Decorador de Request.fail para usarlo como argumento del método 
    updateRequest de la clase Database.

    Llama al método fail del pedido dado.

    Parámetros
    ----------
    req : Request
        Instancia de Request sobre la que se llama a fail.
    args : tuple
        Requerido por el formato de decorador, no se utiliza.
    
    Retorno
    -------
    on_fail : None
        Requerido por el formato de decorador, se devuelve None porque no se 
        modifica ningún producto.
    '''

    req.fail()
    return None