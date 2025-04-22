import unittest
import os
import uuid

import request
from controller.database import Database
from state import ClientState, RequestState

class TestDatabase(unittest.TestCase):
    def setUp(self) -> None:
        self.db = Database('prueba.db')

        # Introduce algunos datos en la base de datos
        self.db.registerClient('pepe')
        self.db.updateClient('pepe', ClientState.SIGNED_IN)
        self.req = request.Request('pepe', request.productsFromString('lapiz'))
        self.db.addRequest(self.req)
        self.db.updateClient('pepe', ClientState.SIGNED_OUT)
    
    def tearDown(self) -> None:
        self.db.close()
        os.remove('prueba.db')
    
    def test_getClientState(self):
        self.assertEqual(self.db.getClientState('carlos'), ClientState.NOT_REGISTERED)
        self.assertEqual(self.db.getClientState('pepe'), ClientState.SIGNED_OUT)
        self.db.updateClient('pepe', ClientState.SIGNED_IN)
        self.assertEqual(self.db.getClientState('pepe'), ClientState.SIGNED_IN)

    def test_registerClient(self):
        # Cliente ya registrado da fallo
        self.assertEqual(self.db.registerClient('pepe'), -1)

        # Cliente sin registrar retorna número de filas añadidas (1)
        self.assertEqual(self.db.registerClient('carlos'), 1)
        # El cliente nuevo empieza con la sesión cerrada
        self.assertEqual(self.db.getClientState('carlos'), ClientState.SIGNED_OUT)

    def test_updateClient(self):
        # Cliente sin registrar no se puede actualizar
        self.assertEqual(self.db.updateClient('carlos', ClientState.SIGNED_IN), -1)
        # No se puede cambiar un cliente registrado a NOT_REGISTERED
        self.assertEqual(self.db.updateClient('pepe', ClientState.NOT_REGISTERED), -1)
        # No se puede cambiar un cliente a un estado en el que ya está
        self.assertEqual(self.db.updateClient('pepe', ClientState.SIGNED_OUT), -1)
        # Caso correcto
        self.assertEqual(self.db.updateClient('pepe', ClientState.SIGNED_IN), 1)
        self.assertEqual(self.db.updateClient('pepe', ClientState.SIGNED_OUT), 1)

    def test_getRequest(self):
        r = self.db.getRequest(self.req.getId())
        self.assertIsNotNone(r)
        self.assertEqual(r.getId(), self.req.getId())
        self.assertEqual(r.getClient(), self.req.getClient())
        self.assertEqual(r.getState(), self.req.getState())
        self.assertListEqual(r.getProducts(), self.req.getProducts())
        
        # Pedido no existente
        other_id = uuid.UUID(int=r.getId().int + 1)
        self.assertIsNone(self.db.getRequest(other_id))
    
    def test_addRequest(self):
        # Ya existe un pedido con esa Id
        self.assertEqual(self.db.addRequest(self.req), -1)

        # Cliente no registrado
        r = request.Request('carlos', request.productsFromString('papel'))
        self.assertEqual(self.db.addRequest(r), -1)

        # Cliente sin sesión iniciada
        r = request.Request('pepe', request.productsFromString('papel'))
        self.assertEqual(self.db.addRequest(r), -1)

        # Caso correcto
        self.db.updateClient('pepe', ClientState.SIGNED_IN)
        self.assertEqual(self.db.addRequest(r), 1)

    def test_updateRequest(self):
        # Cambio solicitado por cliente que no coincide con el que realizó el pedido
        r = self.db.updateRequest(self.req.getId(), request.on_cancel, user_id='carlos')
        self.assertIsNone(r)

        # Cambio solicitado por cliente sin sesión iniciada
        r = self.db.updateRequest(self.req.getId(), request.on_cancel, user_id='pepe')
        self.assertIsNone(r)

        # Caso correcto
        r = self.db.updateRequest(self.req.getId(), request.on_moved, args=(request.Product('lapiz'),))
        self.assertIsNotNone(r)
        self.assertEqual(r.getId(), self.req.getId())
        self.assertEqual(r.getClient(), self.req.getClient())
        self.assertEqual(r.getState(), RequestState.IN_CONVEYOR)

        # Pedido inexistente
        other_id = uuid.UUID(int=r.getId().int + 1)
        r = self.db.updateRequest(other_id, request.on_moved, args=(request.Product('lapiz'),))
        self.assertIsNone(r)

    def test_getClientRequests(self):
        req_list = self.db.getClientRequests('carlos')
        self.assertEqual(len(req_list), 0)

        req_list = self.db.getClientRequests('pepe')
        self.assertEqual(len(req_list), 1)
        r = req_list[0]
        self.assertEqual(r.getId(), self.req.getId())
        self.assertEqual(r.getClient(), self.req.getClient())
        self.assertEqual(r.getState(), self.req.getState())
        self.assertListEqual(r.getProducts(), self.req.getProducts())
