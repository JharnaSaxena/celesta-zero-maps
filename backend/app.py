import mimetypes
import os
from pathlib import Path
from flask import Flask, jsonify, request, send_file, send_from_directory
from backend.config import DEBUG, SERVER_HOST, SERVER_PORT, BACKEND_DIR, BASE_DIR
from backend.database import init_db

# Ensure correct MIME types on Windows
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("application/json", ".json")
mimetypes.add_type("image/jpeg", ".jpg")
mimetypes.add_type("image/jpeg", ".jpeg")

# Route blueprints
from backend.routes.terrain_routes import terrain_bp
from backend.routes.lifeline_routes import lifeline_bp
from backend.routes.sites_routes import sites_bp
from backend.routes.routing_routes import routing_bp
from backend.routes.telemetry_routes import telemetry_bp
from backend.routes.weather_routes import weather_bp
from backend.routes.minerals_routes import minerals_bp
from backend.routes.earth_routes import earth_bp
from backend.routes.system_routes import system_bp
from backend.routes.ephemeris_routes import ephemeris_bp

def create_app():
    app = Flask(__name__, static_folder=None)

    # Initialize SQLite database
    init_db()

    # Enable CORS for all routes and methods
    @app.after_request
    def set_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
        return response

    # Handle OPTIONS preflight requests
    @app.route("/", defaults={"path": ""}, methods=["OPTIONS"])
    @app.route("/<path:path>", methods=["OPTIONS"])
    def options_handler(path):
        return "", 204

    # Register Blueprints
    app.register_blueprint(terrain_bp)
    app.register_blueprint(lifeline_bp)
    app.register_blueprint(sites_bp)
    app.register_blueprint(routing_bp)
    app.register_blueprint(telemetry_bp)
    app.register_blueprint(weather_bp)
    app.register_blueprint(minerals_bp)
    app.register_blueprint(earth_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(ephemeris_bp)

    # 1. Main Cloned Frontend - TerraScope Mars Jezero Explorer
    @app.route("/", methods=["GET"])
    @app.route("/index.html", methods=["GET"])
    def serve_frontend_index():
        return send_file(str(BASE_DIR / "index.html"))

    # 2. Earth Explorer Prototype
    @app.route("/earth", methods=["GET"])
    @app.route("/earth.html", methods=["GET"])
    def serve_earth_explorer():
        return send_file(str(BASE_DIR / "earth.html"))

    # 3. Interactive Swagger API Docs & Mission Control Dashboard
    @app.route("/docs", methods=["GET"])
    def documentation_portal():
        docs_file = BACKEND_DIR / "static" / "docs.html"
        return send_file(str(docs_file))

    # 4. Static asset routes for the frontend
    @app.route("/src/<path:filename>", methods=["GET"])
    def serve_src_files(filename):
        return send_from_directory(str(BASE_DIR / "src"), filename)

    @app.route("/mars/<path:filename>", methods=["GET"])
    def serve_mars_images(filename):
        return send_from_directory(str(BASE_DIR / "public" / "mars"), filename)

    @app.route("/public/<path:filename>", methods=["GET"])
    def serve_public_files(filename):
        return send_from_directory(str(BASE_DIR / "public"), filename)

    @app.route("/data/<path:filename>", methods=["GET"])
    def serve_data_files(filename):
        return send_from_directory(str(BASE_DIR / "data"), filename)

    # Error Handlers
    @app.errorhandler(404)
    def not_found(error):
        # If API route, return JSON error
        if request.path.startswith("/api/"):
            return jsonify({
                "error": "Not Found",
                "message": "The requested API endpoint does not exist. Visit /docs for the API reference.",
                "path": request.path
            }), 404
        # Otherwise fallback to index.html for SPA navigation
        return send_file(str(BASE_DIR / "index.html"))

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred while processing the telemetry or terrain query."
        }), 500

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "error": "Bad Request",
            "message": "Invalid parameters or request payload."
        }), 400

    return app

app = create_app()

if __name__ == "__main__":
    print(f"\n🚀 Jezero Crater Mission Operations & Full-Stack Explorer running at http://{SERVER_HOST}:{SERVER_PORT}")
    print(f"🌍 3D Mars Explorer UI:     http://localhost:{SERVER_PORT}")
    print(f"📖 Interactive API Docs:    http://localhost:{SERVER_PORT}/docs\n")
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=DEBUG)
