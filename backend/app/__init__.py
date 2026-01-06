from flask import Flask, send_from_directory
from flask_cors import CORS
from pathlib import Path

def create_app():
    # Set static folder for frontend files
    app = Flask(__name__, static_folder='static', static_url_path='')
    app.config.from_object('app.config.Config')

    CORS(app)

    # Register database teardown
    from app import database
    app.teardown_appcontext(database.close_db)

    # Initialize database if it doesn't exist
    with app.app_context():
        from app.config import Config

        # Download published database from R2 when using CDN (for fly.io deployment)
        if Config.USE_CDN:
            database.download_published_db_from_r2()

        # Initialize database
        database.init_db()

        # Auto-sync photos on startup when not using CDN
        if not Config.USE_CDN:
            from app.photo_service import PhotoService
            photo_service = PhotoService()
            result = photo_service.sync_database()
            print(f"Auto-sync on startup: added {result['added']}, removed {result['removed']}")

    # Register API routes
    from app import routes
    app.register_blueprint(routes.bp)

    # Serve frontend static files - catch-all route for SPA
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        """Serve frontend files or index.html for SPA routing"""
        # Skip if this is an API request (already handled by blueprint)
        if path.startswith('api/'):
            return {'error': 'Not found'}, 404

        static_folder = Path(app.static_folder) if app.static_folder else None

        # Check if static folder exists
        if not static_folder or not static_folder.exists():
            return {'error': 'Frontend not built. Run: cd ../frontend && npm run build'}, 500

        # If path exists, serve it
        if path and (static_folder / path).exists():
            return send_from_directory(app.static_folder, path)

        # Otherwise serve index.html (SPA routing)
        index_path = static_folder / 'index.html'
        if index_path.exists():
            return send_from_directory(app.static_folder, 'index.html')
        else:
            return {'error': 'Frontend not built. Run: cd ../frontend && npm run build'}, 500

    return app
