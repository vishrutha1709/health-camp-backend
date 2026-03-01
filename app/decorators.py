from functools import wraps
from flask import request, jsonify, g
from app.extensions import get_supabase_client

def protected(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header.split(" ")[1]
        supabase = get_supabase_client()

        try:
            # Verify token and get user
            user_response = supabase.auth.get_user(token)
            if not user_response.user:
                return jsonify({"error": "Invalid or expired token"}), 401

            g.current_user = user_response.user

            # Get role from public.users table
            role_response = supabase.table('users')\
                .select('role')\
                .eq('id', user_response.user.id)\
                .single()\
                .execute()

            g.current_user.role = role_response.data.get('role', 'user') if role_response.data else 'user'

            return f(*args, **kwargs)

        except Exception as e:
            return jsonify({"error": str(e)}), 401

    return decorated_function