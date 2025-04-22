import unittest
import uuid

import request
from state import ProductState, RequestState

class TestProduct(unittest.TestCase):

    def test_init(self):
        p = request.Product('lapiz')
        self.assertEqual(p.getName(), 'lapiz')
        self.assertEqual(p.getState(), ProductState.UNDEFINED)
    
    def test_found(self):
        p = request.Product('lapiz')
        self.assertEqual(p.found(), ProductState.FOUND)
        p = request.Product('papel')
        p.notFound()
        self.assertNotEqual(p.found(), ProductState.FOUND)
    
    def test_notFound(self):
        p = request.Product('lapiz')
        self.assertEqual(p.notFound(), ProductState.NOT_FOUND)
        p = request.Product('papel')
        p.found()
        self.assertNotEqual(p.notFound(), ProductState.NOT_FOUND)
    
    def test_productFromDB(self):
        p = request.Product.productFromDB('lapiz', ProductState.FOUND)
        self.assertEqual(p.getName(), 'lapiz')
        self.assertEqual(p.getState(), ProductState.FOUND)
    
    def test_productsFromString(self):
        prods = request.productsFromString('lapiz papel')
        self.assertEqual(len(prods), 2)
        self.assertEqual(prods[0], request.Product('lapiz'))
        self.assertEqual(prods[1], request.Product('papel'))

class TestRequest(unittest.TestCase):
    def setUp(self) -> None:
        self.req = request.Request('pepe', request.productsFromString('lapiz'))

    def test_init(self):
        self.assertEqual(self.req.getClient(), 'pepe')
        self.assertEqual(self.req.getState(), RequestState.IN_STORAGE)
        self.assertIsInstance(self.req.getId(), uuid.UUID)
        self.assertListEqual(self.req.getProducts(), request.productsFromString('lapiz'))
    
    def test_requestInfo(self):
        # Regex que hace match con una id de un Request
        id_regex = '[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}'
        self.assertRegex(self.req.requestInfo(), 'pepe ' + id_regex + ' lapiz')
    
    def test_found(self):
        self.assertIsNone(self.req.found(request.Product('papel')))
        p = self.req.found(request.Product('lapiz'))
        self.assertIsNotNone(p)
        self.assertEqual(p.getName(), 'lapiz')
        self.assertEqual(p.getState(), ProductState.FOUND)
        
        # Resetea el pedido para hacer más pruebas
        self.setUp()
        self.req.notFound(request.Product('lapiz'))
        self.assertIsNone(self.req.found(request.Product('lapiz')))

    def test_notFound(self):
        self.assertIsNone(self.req.notFound(request.Product('papel')))
        p = self.req.notFound(request.Product('lapiz'))
        self.assertIsNotNone(p)
        self.assertEqual(p.getName(), 'lapiz')
        self.assertEqual(p.getState(), ProductState.NOT_FOUND)
        self.assertEqual(self.req.getState(), RequestState.FAILED)
        
        # Resetea el pedido para hacer más pruebas
        self.setUp()
        self.req.found(request.Product('lapiz'))
        self.assertIsNone(self.req.notFound(request.Product('lapiz')))
    
    def test_cancel(self):
        self.assertEqual(self.req.cancel(), RequestState.CANCELLED)

        # Resetea el pedido para hacer más pruebas
        self.setUp()
        self.req.found(request.Product('lapiz'))
        self.req.move()
        self.assertNotEqual(self.req.cancel(), RequestState.CANCELLED)
        self.req.deliver()
        self.assertNotEqual(self.req.cancel(), RequestState.CANCELLED)

        # Resetea el pedido para hacer más pruebas
        self.setUp()
        self.req.fail()
        self.assertNotEqual(self.req.cancel(), RequestState.CANCELLED)
    
    def test_areProductsPacked(self):
        self.req = request.Request('pepe', request.productsFromString('lapiz papel'))
        self.assertFalse(self.req.areProductsPacked())
        self.req.found(request.Product('lapiz'))
        self.assertFalse(self.req.areProductsPacked())
        self.req.found(request.Product('papel'))
        self.assertTrue(self.req.areProductsPacked())
    
    def test_move(self):
        self.req = request.Request('pepe', request.productsFromString('lapiz papel'))
        self.assertNotEqual(self.req.move(), RequestState.IN_CONVEYOR)
        self.req.found(request.Product('lapiz'))
        self.assertNotEqual(self.req.move(), RequestState.IN_CONVEYOR)
        self.req.found(request.Product('papel'))
        self.assertEqual(self.req.move(), RequestState.IN_CONVEYOR)

        # Resetea el pedido para hacer más pruebas
        self.setUp()
        self.req.cancel()
        self.assertNotEqual(self.req.move(), RequestState.IN_CONVEYOR)

        # Resetea el pedido para hacer más pruebas
        self.setUp()
        self.req.fail()
        self.assertNotEqual(self.req.move(), RequestState.IN_CONVEYOR)

    def test_fail(self):
        self.assertEqual(self.req.fail(), RequestState.FAILED)

        # Resetea el pedido para hacer más pruebas
        self.setUp()
        self.req.found(request.Product('lapiz'))
        self.req.move()
        self.assertEqual(self.req.fail(), RequestState.FAILED)

        # Resetea el pedido para hacer más pruebas
        self.setUp()
        self.req.found(request.Product('lapiz'))
        self.req.move()
        self.req.deliver()
        self.assertNotEqual(self.req.fail(), RequestState.FAILED)

        # Resetea el pedido para hacer más pruebas
        self.setUp()
        self.req.cancel()
        self.assertNotEqual(self.req.fail(), RequestState.FAILED)

    def test_deliver(self):
        self.assertNotEqual(self.req.deliver(), RequestState.DELIVERED)
        self.req.found(request.Product('lapiz'))
        self.req.move()
        self.assertEqual(self.req.deliver(), RequestState.DELIVERED)

        # Resetea el pedido para hacer más pruebas
        self.setUp()
        self.req.cancel()
        self.assertNotEqual(self.req.deliver(), RequestState.DELIVERED)

        # Resetea el pedido para hacer más pruebas
        self.setUp()
        self.req.fail()
        self.assertNotEqual(self.req.deliver(), RequestState.DELIVERED)
    
    def test_stateIsTemporary(self):
        # IN_STORAGE es temporal
        self.assertTrue(self.req.stateIsTemporary())
        self.req.found(request.Product('lapiz'))
        self.req.move()
        # IN_CONVEYOR es temporal
        self.assertTrue(self.req.stateIsTemporary())
        self.req.deliver()
        # DELIVERED no es temporal, es definitivo
        self.assertFalse(self.req.stateIsTemporary())
        
        # Resetea el pedido para hacer más pruebas
        self.setUp()
        self.req.cancel()
        # CANCELLED no es temporal, es definitivo
        self.assertFalse(self.req.stateIsTemporary())
        
        # Resetea el pedido para hacer más pruebas
        self.setUp()
        self.req.fail()
        # FAILED no es temporal, es definitivo
        self.assertFalse(self.req.stateIsTemporary())

    def test_requestFromDB(self):
        self.req = request.Request.requestFromDB(
            client='pepe', 
            products=request.productsFromString('lapiz'),
            id=uuid.UUID('01234567-89ab-cdef-0123-456789abcdef'),
            state=RequestState.CANCELLED
        )
        self.assertEqual(self.req.getClient(), 'pepe')
        self.assertEqual(self.req.getState(), RequestState.CANCELLED)
        self.assertEqual(self.req.getId(), uuid.UUID('01234567-89ab-cdef-0123-456789abcdef'))
        self.assertListEqual(self.req.getProducts(),request.productsFromString('lapiz'))

if __name__ == '__main__':
    unittest.main()