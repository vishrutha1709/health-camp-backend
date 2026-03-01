from flask import Blueprint, jsonify
import app.extensions as extensions  # ← import the module, not the variable

main_bp = Blueprint('main', __name__)
 
@main_bp.route('/health', methods=['GET'])
def health_check():
    try:
        client = extensions.get_supabase_client()      # ← get the client here

        result = client.table('health_camps').select('id').limit(1).execute()
        return jsonify({
            "status": "healthy",
            "supabase_connected": True,
            "message": "Flask backend is running and connected to Supabase successfully! 🎉",
            "health_camps_sample_count": len(result.data)
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "supabase_connected": False,
            "message": str(e),
            "hint": "Check Supabase config or database connection"
        }), 500
    

from app.decorators import protected

@main_bp.route('/protected-test', methods=['GET'])
@protected
def protected_test():
    return jsonify({
        "message": "You are authenticated!",
        "user_id": str(g.current_user.id),
        "role": g.current_user.role
    }), 200