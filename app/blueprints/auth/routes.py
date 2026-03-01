from flask import Blueprint, request, jsonify
from supabase import Client
from app.extensions import get_supabase_client
from flask import g

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')
    phone = data.get('phone')

    if not all([email, password, full_name]):
        return jsonify({"error": "email, password, full_name required"}), 400

    supabase: Client = get_supabase_client()

    try:
        auth_response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": {"full_name": full_name, "phone": phone or None}}
        })

        if not auth_response.user:
            return jsonify({"error": auth_response.error.message}), 400

        user_id = auth_response.user.id

        supabase.table('users').insert({
            "id": str(user_id),
            "email": email,
            "full_name": full_name,
            "phone": phone,
            "role": "user"
        }).execute()

        return jsonify({
            "message": "User created",
            "user_id": str(user_id),
            "email": email
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({"error": "email and password required"}), 400

    supabase: Client = get_supabase_client()

    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if not auth_response.user:
            return jsonify({"error": "Invalid credentials"}), 401

        user_id = str(auth_response.user.id)

        # ── Fetch role + full_name from users table ────────
        user_data = supabase.table('users')\
            .select('full_name, role, phone')\
            .eq('id', user_id)\
            .single()\
            .execute()

        role = 'user'
        full_name = email
        phone = None

        if user_data.data:
            role = user_data.data.get('role', 'user')
            full_name = user_data.data.get('full_name', email)
            phone = user_data.data.get('phone')

        return jsonify({
            "message": "Login successful",
            "access_token": auth_response.session.access_token,
            "user": {
                "id": user_id,
                "email": auth_response.user.email,
                "full_name": full_name,
                "phone": phone,
                "role": role          # ← now correctly returned
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 401


@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Missing or invalid Authorization header"}), 401

    token = auth_header.split(" ")[1]
    supabase = get_supabase_client()

    try:
        user = supabase.auth.get_user(token)
        if not user:
            return jsonify({"error": "Invalid or expired token"}), 401

        user_data = supabase.table('users')\
            .select('*')\
            .eq('id', user.user.id)\
            .single()\
            .execute()

        if not user_data.data:
            return jsonify({"error": "User data not found"}), 404

        return jsonify({
            "user": {
                "id": str(user.user.id),
                "email": user.user.email,
                "full_name": user_data.data.get('full_name'),
                "phone": user_data.data.get('phone'),
                "role": user_data.data.get('role', 'user')
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 401