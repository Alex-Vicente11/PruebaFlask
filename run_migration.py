#!/usr/bin/env python3
"""
Script para ejecutar migraciones de base de datos
Funciona en Windows, macOS y Linux
"""

import os
import sys
from dotenv import load_dotenv
import pymysql

# Cargar variables de entorno
load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'list_products')

def run_migration(migration_file):
    """Ejecuta un archivo de migración SQL"""

    # Verificar que el archivo existe
    if not os.path.exists(migration_file):
        print(f"❌ Error: El archivo {migration_file} no existe")
        sys.exit(1)

    # Leer el archivo SQL
    print(f"📖 Leyendo archivo: {migration_file}")
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Dividir en statements individuales (separados por ;)
    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]

    try:
        # Conectar a la base de datos
        print(f"🔌 Conectando a MySQL en {DB_HOST}:{DB_PORT}")
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        print(f"✅ Conectado a la base de datos: {DB_NAME}")

        with connection.cursor() as cursor:
            # Ejecutar cada statement
            for i, statement in enumerate(statements, 1):
                try:
                    print(f"⚙️  Ejecutando statement {i}/{len(statements)}...")
                    cursor.execute(statement)
                    print(f"   ✓ Completado")
                except Exception as e:
                    print(f"   ⚠️  Error en statement {i}: {e}")
                    # Continuar con el siguiente statement

            # Commit de los cambios
            connection.commit()
            print(f"\n✅ Migración completada exitosamente!")
            print(f"   Total de statements ejecutados: {len(statements)}")

    except pymysql.Error as e:
        print(f"❌ Error de MySQL: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        sys.exit(1)
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()
            print("🔌 Conexión cerrada")

def main():
    """Función principal"""
    print("=" * 60)
    print("🚀 SCRIPT DE MIGRACIÓN DE BASE DE DATOS")
    print("=" * 60)
    print()

    # Por defecto ejecutar la migración 001
    migration_file = 'migrations/001_add_guest_support.sql'

    # Si se proporciona un argumento, usarlo como archivo de migración
    if len(sys.argv) > 1:
        migration_file = sys.argv[1]

    print(f"📁 Archivo de migración: {migration_file}")
    print(f"🗄️  Base de datos: {DB_NAME}")
    print(f"👤 Usuario: {DB_USER}")
    print()

    # Confirmar antes de ejecutar
    response = input("¿Deseas continuar con la migración? (s/n): ")
    if response.lower() not in ['s', 'si', 'yes', 'y']:
        print("❌ Migración cancelada por el usuario")
        sys.exit(0)

    print()
    run_migration(migration_file)

    print()
    print("=" * 60)
    print("✨ PROCESO COMPLETADO")
    print("=" * 60)

if __name__ == '__main__':
    main()
