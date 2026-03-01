from flask import Blueprint, request, jsonify, g
from app.extensions import get_supabase_client
from datetime import datetime
from werkzeug.utils import secure_filename
from app.decorators import protected
import os

camps_bp = Blueprint('camps', __name__)

@camps_bp.route('/', methods=['POST'])
@protected
def create_camp():
    if g.current_user.role != 'admin':
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json()
    required = ['title', 'latitude', 'longitude', 'camp_date', 'camp_time']
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    supabase = get_supabase_client()

    try:
        insert_data = {
            "title": data['title'],
            "description": data.get('description'),
            "latitude": float(data['latitude']),
            "longitude": float(data['longitude']),
            "camp_date": data['camp_date'],
            "camp_time": data['camp_time'],
            "ambulances_available": int(data.get('ambulances_available', 0)),
            "doctors_available": int(data.get('doctors_available', 0)),
            "nearby_hospitals": data.get('nearby_hospitals', []),
            "registration_url": data.get('registration_url'),
            "image_url": data.get('image_url'),
            "created_by": str(g.current_user.id)
        }

        response = supabase.table('health_camps').insert(insert_data).execute()

        return jsonify({
            "message": "Camp created successfully",
            "camp_id": response.data[0]['id']
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@camps_bp.route('/', methods=['GET'])
def get_all_camps():
    supabase = get_supabase_client()
    try:
        response = supabase.table('health_camps')\
            .select("*")\
            .order('camp_date', desc=False)\
            .execute()
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@camps_bp.route('/<camp_id>', methods=['GET'])
def get_camp(camp_id):
    supabase = get_supabase_client()
    try:
        response = supabase.table('health_camps')\
            .select("*")\
            .eq('id', camp_id)\
            .execute()

        if not response.data:
            return jsonify({"error": "Camp not found"}), 404

        return jsonify(response.data[0]), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@camps_bp.route('/<camp_id>', methods=['PUT'])
@protected
def update_camp(camp_id):
    if g.current_user.role != 'admin':
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json()
    supabase = get_supabase_client()

    try:
        response = supabase.table('health_camps')\
            .update(data)\
            .eq('id', camp_id)\
            .execute()

        if not response.data:
            return jsonify({"error": "Camp not found"}), 404

        return jsonify({"message": "Camp updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@camps_bp.route('/<camp_id>', methods=['DELETE'])
@protected
def delete_camp(camp_id):
    if g.current_user.role != 'admin':
        return jsonify({"error": "Admin access required"}), 403

    supabase = get_supabase_client()

    try:
        response = supabase.table('health_camps')\
            .delete()\
            .eq('id', camp_id)\
            .execute()

        if response.data is None or len(response.data) == 0:
            return jsonify({"error": "Camp not found"}), 404

        return jsonify({"message": "Camp deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@camps_bp.route('/<camp_id>/image', methods=['POST'])
@protected
def upload_camp_image(camp_id):
    if g.current_user.role != 'admin':
        return jsonify({"error": "Admin access required"}), 403

    if 'image' not in request.files:
        return jsonify({"error": "No image file part"}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        filename = secure_filename(file.filename)
        unique_filename = f"camp_{camp_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"

        supabase = get_supabase_client()

        try:
            file_path = f"camps/{unique_filename}"
            upload_response = supabase.storage.from_('camps').upload(
                path=file_path,
                file=file.read(),
                file_options={"content-type": file.content_type}
            )

            if upload_response is None or (hasattr(upload_response, 'error') and upload_response.error is not None):
                error_msg = str(upload_response.error) if hasattr(upload_response, 'error') else "Unknown upload error"
                return jsonify({"error": "Upload failed", "details": error_msg}), 500

            public_url = supabase.storage.from_('camps').get_public_url(file_path)

            update_response = supabase.table('health_camps')\
                .update({"image_url": public_url})\
                .eq('id', camp_id)\
                .execute()

            if not update_response.data:
                return jsonify({"error": "Camp not found"}), 404

            return jsonify({
                "message": "Image uploaded successfully",
                "image_url": public_url,
                "camp_id": camp_id
            }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500