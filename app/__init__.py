from flask import Flask
from flask_cors import CORS
from .config import Config
from .extensions import get_supabase_client
from .blueprints.main.routes import main_bp
from .blueprints.auth.routes import auth_bp
from .blueprints.camps.routes import camps_bp
from .blueprints.registrations.routes import registrations_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)

    app.url_map.strict_slashes = False  # ← fixes ALL trailing slash 404s globally

    app.register_blueprint(main_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(camps_bp, url_prefix='/api/camps')
    app.register_blueprint(registrations_bp, url_prefix='/api/registrations')

    @app.route('/')
    def index():
        return {"message": "Health Camp Registration API is running!", "status": "ok"}, 200

    return app