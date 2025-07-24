import unittest
import json
import pymysql
from app import app, get_db_connection

class TestApp(unittest.TestCase):
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        
        # Limpiar y preparar datos de prueba
        self.clean_test_data()
        self.setup_test_data()
    
    def tearDown(self):
        self.clean_test_data()
    
    def clean_test_data(self):
        """Limpia los datos de prueba"""
        try:
            connection = get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM products WHERE product LIKE 'Test%'")
                cursor.execute("DELETE FROM user WHERE user_name LIKE 'Test%'")
                connection.commit()
            connection.close()
        except:
            pass
    
    def setup_test_data(self):
        """Prepara datos iniciales para las pruebas"""
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Insertar un producto de prueba con ID específico
            cursor.execute("INSERT INTO products (id_product, product, price) VALUES (100, 'Test Product Base', 25.50)")
            # Insertar un usuario de prueba con ID específico
            cursor.execute("INSERT INTO user (id_user, user_name) VALUES (200, 'Test User Base')")
            connection.commit()
        connection.close()
    
    def test_create_product_auto_id(self):
        """Prueba que el ID se autogenere correctamente"""
        # Datos de prueba
        product_data = {
            'product': 'Test Product Auto ID',
            'price': 15.99
        }
        
        # Hacer la petición POST
        response = self.app.post('/products', 
                               data=json.dumps(product_data),
                               content_type='application/json')
        
        # Verificar respuesta
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.data)
        self.assertIn('message', response_data)
        self.assertIn('id', response_data)
        
        # Verificar que el producto se insertó en la base de datos
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM products WHERE product = %s", ('Test Product Auto ID',))
            product = cursor.fetchone()
            self.assertIsNotNone(product)
            self.assertEqual(product['product'], 'Test Product Auto ID')
            self.assertEqual(float(product['price']), 15.99)
            # El ID debe ser mayor al último ID existente
            self.assertGreater(product['id_product'], 100)
        connection.close()
    
    def test_create_multiple_products_sequential_ids(self):
        """Prueba que múltiples productos tengan IDs secuenciales"""
        products = [
            {'product': 'Test Product 1', 'price': 10.00},
            {'product': 'Test Product 2', 'price': 20.00},
            {'product': 'Test Product 3', 'price': 30.00}
        ]
        
        created_ids = []
        
        for product_data in products:
            response = self.app.post('/products',
                                   data=json.dumps(product_data),
                                   content_type='application/json')
            self.assertEqual(response.status_code, 201)
            
            # Obtener el ID del producto creado
            connection = get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT id_product FROM products WHERE product = %s", (product_data['product'],))
                result = cursor.fetchone()
                created_ids.append(result['id_product'])
            connection.close()
        
        # Verificar que los IDs son secuenciales
        for i in range(1, len(created_ids)):
            self.assertEqual(created_ids[i], created_ids[i-1] + 1)
    
    def test_create_product_missing_fields(self):
        """Prueba validación de campos requeridos"""
        # Faltan campos
        incomplete_data = {'product': 'Test Product Incomplete'}
        
        response = self.app.post('/products',
                               data=json.dumps(incomplete_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertIn('error', response_data)
        self.assertIn('Faltan campos requeridos', response_data['error'])
    
    def test_create_product_empty_data(self):
        """Prueba con datos vacíos"""
        response = self.app.post('/products',
                               data=json.dumps({}),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertIn('error', response_data)
    
    def test_get_products(self):
        """Prueba obtener todos los productos"""
        response = self.app.get('/products')
        self.assertEqual(response.status_code, 200)
        
        products = json.loads(response.data)
        self.assertIsInstance(products, list)
        # Debe incluir al menos el producto base de prueba
        self.assertGreaterEqual(len(products), 1)
    
    def test_create_user_auto_id(self):
        """Prueba que el ID de usuario se autogenere correctamente"""
        # Datos de prueba
        user_data = {
            'user_name': 'Test User Auto ID'
        }
        
        # Hacer la petición POST
        response = self.app.post('/users', 
                               data=json.dumps(user_data),
                               content_type='application/json')
        
        # Verificar respuesta
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.data)
        self.assertIn('message', response_data)
        self.assertIn('id', response_data)
        
        # Verificar que el usuario se insertó en la base de datos
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM user WHERE user_name = %s", ('Test User Auto ID',))
            user = cursor.fetchone()
            self.assertIsNotNone(user)
            self.assertEqual(user['user_name'], 'Test User Auto ID')
            # El ID debe ser mayor al último ID existente
            self.assertGreater(user['id_user'], 200)
        connection.close()
    
    def test_create_multiple_users_sequential_ids(self):
        """Prueba que múltiples usuarios tengan IDs secuenciales"""
        users = [
            {'user_name': 'Test User 1'},
            {'user_name': 'Test User 2'},
            {'user_name': 'Test User 3'}
        ]
        
        created_ids = []
        
        for user_data in users:
            response = self.app.post('/users',
                                   data=json.dumps(user_data),
                                   content_type='application/json')
            self.assertEqual(response.status_code, 201)
            
            # Obtener el ID del usuario creado
            connection = get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT id_user FROM user WHERE user_name = %s", (user_data['user_name'],))
                result = cursor.fetchone()
                created_ids.append(result['id_user'])
            connection.close()
        
        # Verificar que los IDs son secuenciales
        for i in range(1, len(created_ids)):
            self.assertEqual(created_ids[i], created_ids[i-1] + 1)
    
    def test_create_user_missing_fields(self):
        """Prueba validación de campos requeridos para usuarios"""
        # Datos vacíos
        incomplete_data = {}
        
        response = self.app.post('/users',
                               data=json.dumps(incomplete_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertIn('error', response_data)
        self.assertIn('Faltan campos requeridos', response_data['error'])
    
    def test_get_users(self):
        """Prueba obtener todos los usuarios"""
        response = self.app.get('/users')
        self.assertEqual(response.status_code, 200)
        
        users = json.loads(response.data)
        self.assertIsInstance(users, list)
        # Debe incluir al menos el usuario base de prueba
        self.assertGreaterEqual(len(users), 1)

if __name__ == '__main__':
    unittest.main()