"""
Authentication utilities for guest user system
Provides password hashing, JWT token generation, and authentication decorators
"""

import bcrypt
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'change-this-to-a-random-secret-key-in-production')


def hash_password(password):
    """
    Hash a password using bcrypt
    
    Args:
        password (str): Plain text password
        
    Returns:
        str: Hashed password
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password, hashed):
    """
    Verify a password against its hash
    
    Args:
        password (str): Plain text password
        hashed (str): Hashed password from database
        
    Returns:
        bool: True if password matches, False otherwise
    """
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def generate_jwt(user_id, is_guest=False):
    """
    Generate a JWT token for user authentication
    
    Args:
        user_id (int): User ID
        is_guest (bool): Whether the user is a guest
        
    Returns:
        str: JWT token
    """
    payload = {
        'user_id': user_id,
        'is_guest': is_guest,
        'exp': datetime.utcnow() + timedelta(days=30),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')


def decode_jwt(token):
    """
    Decode and verify a JWT token
    
    Args:
        token (str): JWT token
        
    Returns:
        dict: Payload if valid, None otherwise
    """
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def require_auth(f):
    """
    Decorator to protect endpoints requiring authentication
    
    Usage:
        @app.route('/protected')
        @require_auth
        def protected_route():
            user_id = request.user_id
            is_guest = request.is_guest
            return jsonify({'user_id': user_id})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({
                'success': False,
                'message': 'Token missing'
            }), 401

        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]

        payload = decode_jwt(token)
        if not payload:
            return jsonify({
                'success': False,
                'message': 'Invalid or expired token'
            }), 401

        # Add user info to request context
        request.user_id = payload['user_id']
        request.is_guest = payload.get('is_guest', False)

        return f(*args, **kwargs)

    return decorated_function


def optional_auth(f):
    """
    Decorator for endpoints that can work with or without authentication
    If authenticated, adds user_id and is_guest to request
    If not authenticated, these will be None
    
    Usage:
        @app.route('/optional')
        @optional_auth
        def optional_route():
            user_id = getattr(request, 'user_id', None)
            return jsonify({'authenticated': user_id is not None})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')

        if token:
            if token.startswith('Bearer '):
                token = token[7:]

            payload = decode_jwt(token)
            if payload:
                request.user_id = payload['user_id']
                request.is_guest = payload.get('is_guest', False)
            else:
                request.user_id = None
                request.is_guest = None
        else:
            request.user_id = None
            request.is_guest = None

        return f(*args, **kwargs)

    return decorated_function
