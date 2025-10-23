#!/usr/bin/env python3
"""
Script de desarrollo para poblar la base de datos con datos de prueba
Útil para testing y desarrollo de la integración Android
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Agregar el directorio actual al path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app, db, User, Product, Cart
from auth_utils import hash_password
from peewee import fn


class DatabaseSeeder:
    """Clase para poblar la base de datos con datos de prueba"""
    
    def __init__(self):
        self.app = app
        self.created_users = []
        self.created_products = []
        self.created_cart_items = []
        
    def run(self, clean=False):
        """
        Ejecutar el seeding de la base de datos
        
        Args:
            clean (bool): Si True, limpia los datos de prueba antes de crear nuevos
        """
        print("=" * 60)
        print("🌱 DATABASE SEEDER - Iniciando...")
        print("=" * 60)
        
        if clean:
            self.clean_test_data()
        
        self.create_products()
        self.create_users()
        self.create_guest_users()
        self.create_cart_items()
        
        self.print_summary()
        
    def clean_test_data(self):
        """Limpiar datos de prueba existentes"""
        print("\n🧹 Limpiando datos de prueba existentes...")
        
        try:
            # Eliminar carritos de prueba
            Cart.delete().where(
                Cart.id_user.in_(
                    User.select(User.id_user).where(
                        (User.email.contains('test@')) |
                        (User.guest_id.contains('seed_guest'))
                    )
                )
            ).execute()
            
            # Eliminar usuarios de prueba
            deleted_users = User.delete().where(
                (User.email.contains('test@')) |
                (User.guest_id.contains('seed_guest'))
            ).execute()
            
            # Eliminar productos de prueba
            deleted_products = Product.delete().where(
                Product.product.contains('[TEST]')
            ).execute()
            
            print(f"   ✓ {deleted_users} usuarios de prueba eliminados")
            print(f"   ✓ {deleted_products} productos de prueba eliminados")
            
        except Exception as e:
            print(f"   ⚠ Error limpiando datos: {e}")
    
    def create_products(self):
        """Crear productos de prueba"""
        print("\n📦 Creando productos de prueba...")
        
        products_data = [
            {"name": "[TEST] iPhone 15 Pro", "price": 999.99},
            {"name": "[TEST] Samsung Galaxy S24", "price": 899.99},
            {"name": "[TEST] MacBook Air M3", "price": 1299.99},
            {"name": "[TEST] iPad Pro 12.9", "price": 1099.99},
            {"name": "[TEST] AirPods Pro", "price": 249.99},
            {"name": "[TEST] Apple Watch Series 9", "price": 399.99},
            {"name": "[TEST] Magic Keyboard", "price": 149.99},
            {"name": "[TEST] USB-C Cable", "price": 19.99},
            {"name": "[TEST] Wireless Charger", "price": 39.99},
            {"name": "[TEST] Phone Case", "price": 29.99},
        ]
        
        for product_data in products_data:
            try:
                max_id = Product.select(fn.COALESCE(fn.MAX(Product.id_product), 0).alias('max_id')).scalar()
                new_id = max_id + 1
                
                product = Product.create(
                    id_product=new_id,
                    product=product_data["name"],
                    price=product_data["price"]
                )
                
                self.created_products.append(product)
                print(f"   ✓ Creado: {product.product} - ${product.price}")
                
            except Exception as e:
                print(f"   ✗ Error creando producto {product_data['name']}: {e}")
        
        print(f"\n   📦 Total productos creados: {len(self.created_products)}")
    
    def create_users(self):
        """Crear usuarios reales de prueba"""
        print("\n👤 Creando usuarios registrados de prueba...")
        
        users_data = [
            {
                "name": "Test User 1",
                "email": "test1@example.com",
                "password": "password123"
            },
            {
                "name": "Test User 2",
                "email": "test2@example.com",
                "password": "password123"
            },
            {
                "name": "Test User 3",
                "email": "test3@example.com",
                "password": "password123"
            },
            {
                "name": "Admin Test",
                "email": "admin@test.com",
                "password": "admin123"
            },
            {
                "name": "Demo User",
                "email": "demo@example.com",
                "password": "demo123"
            }
        ]
        
        for user_data in users_data:
            try:
                # Verificar si el email ya existe
                existing = User.get_or_none(User.email == user_data["email"])
                if existing:
                    print(f"   ⚠ Usuario ya existe: {user_data['email']}")
                    self.created_users.append(existing)
                    continue
                
                max_id = User.select(fn.COALESCE(fn.MAX(User.id_user), 0).alias('max_id')).scalar()
                new_id = max_id + 1
                
                user = User.create(
                    id_user=new_id,
                    user_name=user_data["name"],
                    email=user_data["email"],
                    password_hash=hash_password(user_data["password"]),
                    is_guest=False,
                    guest_id=None,
                    created_at=datetime.now()
                )
                
                self.created_users.append(user)
                print(f"   ✓ Creado: {user.user_name} ({user.email})")
                
            except Exception as e:
                print(f"   ✗ Error creando usuario {user_data['email']}: {e}")
        
        print(f"\n   👤 Total usuarios registrados: {len([u for u in self.created_users if not u.is_guest])}")
    
    def create_guest_users(self):
        """Crear usuarios invitados de prueba"""
        print("\n👻 Creando usuarios guest de prueba...")
        
        guest_configs = [
            {"days_old": 0, "has_cart": True},   # Guest reciente con carrito
            {"days_old": 1, "has_cart": True},   # Guest de ayer con carrito
            {"days_old": 7, "has_cart": False},  # Guest de hace 1 semana sin carrito
            {"days_old": 15, "has_cart": True},  # Guest de hace 2 semanas con carrito
            {"days_old": 31, "has_cart": False}, # Guest antiguo (para cleanup)
            {"days_old": 35, "has_cart": True},  # Guest muy antiguo con carrito
        ]
        
        for i, config in enumerate(guest_configs, 1):
            try:
                max_id = User.select(fn.COALESCE(fn.MAX(User.id_user), 0).alias('max_id')).scalar()
                new_id = max_id + 1
                
                guest_id = f"seed_guest_{new_id}_{int(datetime.now().timestamp())}"
                created_date = datetime.now() - timedelta(days=config["days_old"])
                
                guest = User.create(
                    id_user=new_id,
                    user_name="Guest User",
                    email=None,
                    password_hash=None,
                    is_guest=True,
                    guest_id=guest_id,
                    created_at=created_date
                )
                
                self.created_users.append(guest)
                
                status = "con carrito" if config["has_cart"] else "sin carrito"
                print(f"   ✓ Guest #{i}: {config['days_old']} días antiguo, {status}")
                
                # Si debe tener carrito, lo agregamos después
                if config["has_cart"]:
                    guest._has_cart = True  # Flag temporal para create_cart_items
                
            except Exception as e:
                print(f"   ✗ Error creando guest #{i}: {e}")
        
        print(f"\n   👻 Total guests creados: {len([u for u in self.created_users if u.is_guest])}")
    
    def create_cart_items(self):
        """Crear items en carritos de prueba"""
        print("\n🛒 Creando items en carritos...")
        
        if not self.created_products:
            print("   ⚠ No hay productos disponibles para crear carritos")
            return
        
        cart_count = 0
        
        # Agregar items a usuarios reales
        real_users = [u for u in self.created_users if not u.is_guest]
        for user in real_users[:3]:  # Solo primeros 3 usuarios
            num_items = random.randint(1, 4)
            selected_products = random.sample(self.created_products, min(num_items, len(self.created_products)))
            
            for product in selected_products:
                try:
                    quantity = random.randint(1, 3)
                    
                    cart_item = Cart.create(
                        id_user=user.id_user,
                        id_product=product.id_product,
                        quantity=quantity,
                        added_date=datetime.now() - timedelta(days=random.randint(0, 5))
                    )
                    
                    self.created_cart_items.append(cart_item)
                    cart_count += 1
                    
                except Exception as e:
                    print(f"   ✗ Error agregando producto al carrito: {e}")
        
        # Agregar items a guests que deben tener carrito
        guests_with_cart = [u for u in self.created_users if u.is_guest and hasattr(u, '_has_cart')]
        for guest in guests_with_cart:
            num_items = random.randint(1, 3)
            selected_products = random.sample(self.created_products, min(num_items, len(self.created_products)))
            
            for product in selected_products:
                try:
                    quantity = random.randint(1, 2)
                    
                    cart_item = Cart.create(
                        id_user=guest.id_user,
                        id_product=product.id_product,
                        quantity=quantity,
                        added_date=guest.created_at + timedelta(hours=random.randint(1, 12))
                    )
                    
                    self.created_cart_items.append(cart_item)
                    cart_count += 1
                    
                except Exception as e:
                    print(f"   ✗ Error agregando producto al carrito guest: {e}")
        
        print(f"\n   🛒 Total items de carrito creados: {cart_count}")
    
    def print_summary(self):
        """Imprimir resumen de datos creados"""
        print("\n" + "=" * 60)
        print("✅ SEEDING COMPLETADO")
        print("=" * 60)
        
        real_users = [u for u in self.created_users if not u.is_guest]
        guest_users = [u for u in self.created_users if u.is_guest]
        
        print(f"\n📊 Resumen:")
        print(f"   • Productos:            {len(self.created_products)}")
        print(f"   • Usuarios registrados: {len(real_users)}")
        print(f"   • Usuarios guest:       {len(guest_users)}")
        print(f"   • Items en carritos:    {len(self.created_cart_items)}")
        
        print(f"\n🔐 Credenciales de prueba:")
        print(f"   Email: test1@example.com | Password: password123")
        print(f"   Email: test2@example.com | Password: password123")
        print(f"   Email: admin@test.com    | Password: admin123")
        print(f"   Email: demo@example.com  | Password: demo123")
        
        if guest_users:
            print(f"\n👻 Guests creados (usar para pruebas de fusión):")
            for i, guest in enumerate(guest_users[:3], 1):
                days_old = (datetime.now() - guest.created_at).days
                has_cart = any(c.id_user == guest.id_user for c in self.created_cart_items)
                cart_status = "✓ con carrito" if has_cart else "sin carrito"
                print(f"   {i}. guest_id: {guest.guest_id}")
                print(f"      → {days_old} días antiguo, {cart_status}")
        
        print(f"\n📦 Productos de prueba disponibles:")
        for i, product in enumerate(self.created_products[:5], 1):
            print(f"   {i}. {product.product} - ${product.price} (ID: {product.id_product})")
        if len(self.created_products) > 5:
            print(f"   ... y {len(self.created_products) - 5} más")
        
        print("\n" + "=" * 60)
        print("🚀 Base de datos lista para pruebas de integración!")
        print("=" * 60)
        print("\n💡 Sugerencias:")
        print("   • Usa los guests para probar registro/login con fusión de carrito")
        print("   • Los guests antiguos (31+ días) sirven para probar cleanup")
        print("   • Usa las credenciales de arriba para probar login desde Android")
        print("   • Los productos [TEST] se pueden eliminar fácilmente después")
        print()


def main():
    """Función principal del script"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Poblar base de datos con datos de prueba'
    )
    parser.add_argument(
        '--clean',
        action='store_true',
        help='Limpiar datos de prueba existentes antes de crear nuevos'
    )
    parser.add_argument(
        '--only-clean',
        action='store_true',
        help='Solo limpiar datos de prueba sin crear nuevos'
    )
    
    args = parser.parse_args()
    
    # Conectar a la base de datos
    try:
        db.connect()
        print("✓ Conectado a la base de datos")
    except Exception as e:
        print(f"✗ Error conectando a la base de datos: {e}")
        sys.exit(1)
    
    seeder = DatabaseSeeder()
    
    try:
        if args.only_clean:
            print("=" * 60)
            print("🧹 LIMPIEZA DE DATOS DE PRUEBA")
            print("=" * 60)
            seeder.clean_test_data()
            print("\n✅ Limpieza completada")
        else:
            seeder.run(clean=args.clean)
    
    except KeyboardInterrupt:
        print("\n\n⚠ Operación cancelada por el usuario")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n✗ Error durante el seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        if not db.is_closed():
            db.close()


if __name__ == '__main__':
    main()
