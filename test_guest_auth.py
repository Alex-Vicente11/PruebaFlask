"""
Unit Tests for Guest User Authentication System
Tests: guest creation, registration, login, cart merge, and cleanup
"""

import unittest
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app, db, User, Cart, Product
from auth_utils import hash_password, verify_password, generate_jwt, decode_jwt


class TestGuestAuthSystem(unittest.TestCase):
    """Test suite for guest user authentication system"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures that are used for all tests"""
        app.config['TESTING'] = True
        app.config['DEBUG'] = False
        cls.client = app.test_client()

    def setUp(self):
        """Set up before each test"""
        self.client = app.test_client()
        
        # Create a test product
        try:
            max_id = Product.select(fn.COALESCE(fn.MAX(Product.id_product), 0).alias('max_id')).scalar()
            self.test_product = Product.create(
                id_product=max_id + 1,
                product='Test Product',
                price=99.99
            )
        except:
            # Product might already exist
            self.test_product = Product.get(Product.product == 'Test Product')

    def tearDown(self):
        """Clean up after each test"""
        # Clean up test users
        User.delete().where(
            (User.user_name == 'Test User') |
            (User.email == 'test@example.com') |
            (User.email == 'test2@example.com') |
            (User.guest_id.startswith('test_guest'))
        ).execute()
        
        # Clean up test cart items
        Cart.delete().where(Cart.id_product == self.test_product.id_product).execute()

    # ==================
    # Guest User Tests
    # ==================

    def test_create_guest_user(self):
        """Test creating a new guest user"""
        response = self.client.post('/api/guest/create', json={
            'guest_id': 'test_guest_12345'
        })
        
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        
        self.assertTrue(data['success'])
        self.assertIsNotNone(data['user_id'])
        self.assertTrue(data['is_guest'])
        self.assertEqual(data['message'], 'Guest user created successfully')

    def test_create_duplicate_guest(self):
        """Test creating guest with existing guest_id returns existing user"""
        guest_id = 'test_guest_duplicate'
        
        # Create first guest
        response1 = self.client.post('/api/guest/create', json={
            'guest_id': guest_id
        })
        data1 = response1.get_json()
        user_id1 = data1['user_id']
        
        # Try to create again
        response2 = self.client.post('/api/guest/create', json={
            'guest_id': guest_id
        })
        data2 = response2.get_json()
        
        self.assertEqual(response2.status_code, 200)
        self.assertTrue(data2['success'])
        self.assertEqual(data2['user_id'], user_id1)  # Same user ID
        self.assertIn('already exists', data2['message'])

    def test_create_guest_missing_guest_id(self):
        """Test creating guest without guest_id returns error"""
        response = self.client.post('/api/guest/create', json={})
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        
        self.assertFalse(data['success'])
        self.assertIn('guest_id is required', data['message'])

    # ==================
    # Registration Tests
    # ==================

    def test_register_new_user(self):
        """Test registering a new user without guest"""
        response = self.client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'password': 'password123',
            'user_name': 'Test User'
        })
        
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        
        self.assertTrue(data['success'])
        self.assertIsNotNone(data['user_id'])
        self.assertFalse(data['is_guest'])
        self.assertIsNotNone(data['token'])
        self.assertFalse(data['cart_migrated'])
        self.assertEqual(data['cart_items_count'], 0)

    def test_register_with_cart_merge(self):
        """Test registering user with guest cart merge"""
        # 1. Create guest
        guest_response = self.client.post('/api/guest/create', json={
            'guest_id': 'test_guest_register'
        })
        guest_data = guest_response.get_json()
        guest_user_id = guest_data['user_id']
        
        # 2. Add item to guest cart
        cart_response = self.client.post('/add-to-cart', json={
            'id_user': guest_user_id,
            'id_product': self.test_product.id_product,
            'quantity': 2
        })
        self.assertTrue(cart_response.get_json()['success'])
        
        # 3. Register user with guest_id
        register_response = self.client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'password': 'password123',
            'user_name': 'Test User',
            'guest_id': 'test_guest_register'
        })
        
        self.assertEqual(register_response.status_code, 201)
        register_data = register_response.get_json()
        
        self.assertTrue(register_data['success'])
        self.assertTrue(register_data['cart_migrated'])
        self.assertEqual(register_data['cart_items_count'], 1)  # 1 unique product
        
        # 4. Verify guest was deleted
        guest_user = User.get_or_none(User.id_user == guest_user_id)
        self.assertIsNone(guest_user)

    def test_register_duplicate_email(self):
        """Test registering with existing email returns error"""
        # Register first user
        self.client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'password': 'password123',
            'user_name': 'Test User'
        })
        
        # Try to register again with same email
        response = self.client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'password': 'different_password',
            'user_name': 'Different User'
        })
        
        self.assertEqual(response.status_code, 409)
        data = response.get_json()
        
        self.assertFalse(data['success'])
        self.assertIn('already registered', data['message'])

    def test_register_invalid_email(self):
        """Test registering with invalid email format returns error"""
        response = self.client.post('/api/auth/register', json={
            'email': 'invalid_email',
            'password': 'password123',
            'user_name': 'Test User'
        })
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        
        self.assertFalse(data['success'])
        self.assertIn('Invalid email format', data['message'])

    def test_register_missing_fields(self):
        """Test registering without required fields returns error"""
        response = self.client.post('/api/auth/register', json={
            'email': 'test@example.com'
            # Missing password
        })
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        
        self.assertFalse(data['success'])
        self.assertIn('required', data['message'])

    # ==================
    # Login Tests
    # ==================

    def test_login_success(self):
        """Test successful login"""
        # Register user first
        self.client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'password': 'password123',
            'user_name': 'Test User'
        })
        
        # Login
        response = self.client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        self.assertTrue(data['success'])
        self.assertIsNotNone(data['token'])
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['user_name'], 'Test User')

    def test_login_with_cart_merge(self):
        """Test login with guest cart merge"""
        # 1. Register user
        register_response = self.client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'password': 'password123',
            'user_name': 'Test User'
        })
        real_user_id = register_response.get_json()['user_id']
        
        # 2. Create guest with cart
        guest_response = self.client.post('/api/guest/create', json={
            'guest_id': 'test_guest_login'
        })
        guest_user_id = guest_response.get_json()['user_id']
        
        self.client.post('/add-to-cart', json={
            'id_user': guest_user_id,
            'id_product': self.test_product.id_product,
            'quantity': 3
        })
        
        # 3. Login with guest_id
        login_response = self.client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'password123',
            'guest_id': 'test_guest_login'
        })
        
        self.assertEqual(login_response.status_code, 200)
        login_data = login_response.get_json()
        
        self.assertTrue(login_data['success'])
        self.assertTrue(login_data['cart_migrated'])
        self.assertEqual(login_data['cart_items_count'], 1)

    def test_login_invalid_credentials(self):
        """Test login with wrong password"""
        # Register user
        self.client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'password': 'password123',
            'user_name': 'Test User'
        })
        
        # Try login with wrong password
        response = self.client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'wrong_password'
        })
        
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        
        self.assertFalse(data['success'])
        self.assertIn('Invalid credentials', data['message'])

    def test_login_nonexistent_user(self):
        """Test login with non-existent email"""
        response = self.client.post('/api/auth/login', json={
            'email': 'nonexistent@example.com',
            'password': 'password123'
        })
        
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        
        self.assertFalse(data['success'])
        self.assertIn('Invalid credentials', data['message'])

    # ==================
    # Cart Merge Tests
    # ==================

    def test_manual_cart_merge(self):
        """Test manual cart merge endpoint"""
        # 1. Create real user
        register_response = self.client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'password': 'password123',
            'user_name': 'Test User'
        })
        real_user_id = register_response.get_json()['user_id']
        token = register_response.get_json()['token']
        
        # 2. Create guest with cart
        guest_response = self.client.post('/api/guest/create', json={
            'guest_id': 'test_guest_manual_merge'
        })
        guest_user_id = guest_response.get_json()['user_id']
        
        self.client.post('/add-to-cart', json={
            'id_user': guest_user_id,
            'id_product': self.test_product.id_product,
            'quantity': 5
        })
        
        # 3. Manual merge
        merge_response = self.client.post('/api/cart/merge',
            headers={'Authorization': f'Bearer {token}'},
            json={'guest_id': 'test_guest_manual_merge'}
        )
        
        self.assertEqual(merge_response.status_code, 200)
        merge_data = merge_response.get_json()
        
        self.assertTrue(merge_data['success'])
        self.assertEqual(merge_data['merged_items'], 1)

    def test_manual_cart_merge_without_token(self):
        """Test manual cart merge without auth token returns 401"""
        response = self.client.post('/api/cart/merge', json={
            'guest_id': 'test_guest_12345'
        })
        
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        
        self.assertFalse(data['success'])
        self.assertIn('Token missing', data['message'])

    def test_manual_cart_merge_guest_not_found(self):
        """Test manual cart merge with non-existent guest returns 404"""
        # Register user and get token
        register_response = self.client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'password': 'password123',
            'user_name': 'Test User'
        })
        token = register_response.get_json()['token']
        
        # Try to merge non-existent guest
        response = self.client.post('/api/cart/merge',
            headers={'Authorization': f'Bearer {token}'},
            json={'guest_id': 'nonexistent_guest'}
        )
        
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        
        self.assertFalse(data['success'])
        self.assertIn('not found', data['message'])

    # ==================
    # Guest Cleanup Tests
    # ==================

    def test_guest_cleanup(self):
        """Test cleanup of old guest users"""
        # Create old guest (mock created_at by updating database directly)
        guest_response = self.client.post('/api/guest/create', json={
            'guest_id': 'test_guest_old'
        })
        guest_user_id = guest_response.get_json()['user_id']
        
        # Update created_at to 31 days ago
        old_date = datetime.now() - timedelta(days=31)
        User.update(created_at=old_date).where(User.id_user == guest_user_id).execute()
        
        # Register user to get auth token
        register_response = self.client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'password': 'password123',
            'user_name': 'Test User'
        })
        token = register_response.get_json()['token']
        
        # Call cleanup
        response = self.client.delete('/api/guest/cleanup',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        self.assertTrue(data['success'])
        self.assertGreaterEqual(data['deleted_guests'], 1)

    def test_guest_cleanup_without_token(self):
        """Test cleanup without auth token returns 401"""
        response = self.client.delete('/api/guest/cleanup')
        
        self.assertEqual(response.status_code, 401)

    # ==================
    # Auth Utils Tests
    # ==================

    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = 'testpassword123'
        hashed = hash_password(password)
        
        self.assertIsNotNone(hashed)
        self.assertNotEqual(password, hashed)
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password('wrong_password', hashed))

    def test_jwt_generation_and_decoding(self):
        """Test JWT token generation and decoding"""
        user_id = 123
        is_guest = False
        
        token = generate_jwt(user_id, is_guest)
        self.assertIsNotNone(token)
        
        payload = decode_jwt(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload['user_id'], user_id)
        self.assertEqual(payload['is_guest'], is_guest)

    def test_jwt_invalid_token(self):
        """Test decoding invalid JWT token returns None"""
        invalid_token = 'invalid.token.here'
        payload = decode_jwt(invalid_token)
        
        self.assertIsNone(payload)

    # ==================
    # Integration Tests
    # ==================

    def test_full_guest_to_registered_flow(self):
        """Test complete flow: guest creation → add to cart → register → cart merged"""
        # 1. Create guest
        guest_response = self.client.post('/api/guest/create', json={
            'guest_id': 'test_guest_full_flow'
        })
        self.assertEqual(guest_response.status_code, 201)
        guest_user_id = guest_response.get_json()['user_id']
        
        # 2. Add product to guest cart
        cart_response = self.client.post('/add-to-cart', json={
            'id_user': guest_user_id,
            'id_product': self.test_product.id_product,
            'quantity': 2
        })
        self.assertTrue(cart_response.get_json()['success'])
        
        # 3. Register with guest_id
        register_response = self.client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'password': 'password123',
            'user_name': 'Test User',
            'guest_id': 'test_guest_full_flow'
        })
        self.assertEqual(register_response.status_code, 201)
        register_data = register_response.get_json()
        
        # Verify cart was merged
        self.assertTrue(register_data['cart_migrated'])
        self.assertEqual(register_data['cart_items_count'], 1)
        
        # 4. Verify cart items exist for new user
        new_user_id = register_data['user_id']
        cart_items = Cart.select().where(Cart.id_user == new_user_id)
        self.assertEqual(cart_items.count(), 1)
        
        # 5. Verify guest was deleted
        guest = User.get_or_none(User.id_user == guest_user_id)
        self.assertIsNone(guest)

    def test_cart_merge_with_duplicate_products(self):
        """Test cart merge when both guest and real user have same product"""
        # 1. Create real user with item in cart
        register_response = self.client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'password': 'password123',
            'user_name': 'Test User'
        })
        real_user_id = register_response.get_json()['user_id']
        
        self.client.post('/add-to-cart', json={
            'id_user': real_user_id,
            'id_product': self.test_product.id_product,
            'quantity': 2
        })
        
        # 2. Create guest with same product
        guest_response = self.client.post('/api/guest/create', json={
            'guest_id': 'test_guest_duplicate_product'
        })
        guest_user_id = guest_response.get_json()['user_id']
        
        self.client.post('/add-to-cart', json={
            'id_user': guest_user_id,
            'id_product': self.test_product.id_product,
            'quantity': 3
        })
        
        # 3. Login with guest_id
        login_response = self.client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'password123',
            'guest_id': 'test_guest_duplicate_product'
        })
        
        # Verify cart was merged
        login_data = login_response.get_json()
        self.assertTrue(login_data['cart_migrated'])
        
        # 4. Verify quantity was summed (2 + 3 = 5)
        cart_item = Cart.get_or_none(
            (Cart.id_user == real_user_id) &
            (Cart.id_product == self.test_product.id_product)
        )
        self.assertIsNotNone(cart_item)
        self.assertEqual(cart_item.quantity, 5)


class TestAuthUtilsStandalone(unittest.TestCase):
    """Standalone tests for auth_utils module"""

    def test_password_hash_is_different_each_time(self):
        """Test that same password generates different hashes (salt)"""
        password = 'test123'
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        self.assertNotEqual(hash1, hash2)
        self.assertTrue(verify_password(password, hash1))
        self.assertTrue(verify_password(password, hash2))

    def test_jwt_expiration(self):
        """Test JWT token contains expiration time"""
        token = generate_jwt(user_id=1, is_guest=False)
        payload = decode_jwt(token)
        
        self.assertIn('exp', payload)
        self.assertIn('iat', payload)
        
        # Check that expiration is ~30 days in the future
        exp_time = datetime.fromtimestamp(payload['exp'])
        iat_time = datetime.fromtimestamp(payload['iat'])
        diff = exp_time - iat_time
        
        # Should be approximately 30 days (allowing some margin)
        self.assertGreater(diff.days, 28)
        self.assertLess(diff.days, 32)


def run_tests():
    """Run all tests and return results"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestGuestAuthSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestAuthUtilsStandalone))
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
