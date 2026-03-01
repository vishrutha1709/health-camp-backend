from flask import Blueprint, request, jsonify, g
from app.extensions import get_supabase_client
from app.decorators import protected

registrations_bp = Blueprint('registrations', __name__)

@registrations_bp.route('/', methods=['POST'])
@protected
def register_for_camp():
    data = request.get_json()
    required = ['camp_id']
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing field: {', '.join(missing)}"}), 400

    # Real user ID from the JWT token
    user_id = str(g.current_user.id)
    camp_id = data['camp_id']

    supabase = get_supabase_client()

    try:
        # Check duplicate
        existing = supabase.table('registrations')\
            .select('id')\
            .eq('user_id', user_id)\
            .eq('camp_id', camp_id)\
            .execute()

        if existing.data:
            return jsonify({"error": "Already registered for this camp"}), 409

        # Register
        response = supabase.table('registrations').insert({
            "user_id": user_id,
            "camp_id": camp_id
        }).execute()

        return jsonify({
            "message": "Registered successfully",
            "registration_id": response.data[0]['id']
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@registrations_bp.route('/my', methods=['GET'])
@protected
def get_my_registrations():
    # Real user ID from the JWT token
    user_id = str(g.current_user.id)

    supabase = get_supabase_client()

    try:
        response = supabase.table('registrations')\
            .select('*, health_camps(*)')\
            .eq('user_id', user_id)\
            .execute()

        return jsonify({
            "registrations": response.data,
            "count": len(response.data)
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500