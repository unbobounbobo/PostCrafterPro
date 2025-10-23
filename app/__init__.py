"""
Flask application factory for PostCrafterPro
"""
from flask import Flask
from config import config


def create_app(config_name='default'):
    """
    Create and configure the Flask application

    Args:
        config_name: Configuration name ('development', 'production', or 'default')

    Returns:
        Flask application instance
    """
    import os

    # Get the base directory (project root)
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    # Create Flask app with correct template and static folders
    app = Flask(
        __name__,
        template_folder=os.path.join(basedir, 'templates'),
        static_folder=os.path.join(basedir, 'static')
    )

    # Load configuration
    app.config.from_object(config[config_name])

    # Validate configuration
    try:
        config[config_name].validate()
    except ValueError as e:
        print(f"Configuration Error: {e}")
        raise

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.api import api_bp
    from app.routes.settings import settings_bp
    from app.routes.batch_api import batch_api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(settings_bp)
    app.register_blueprint(batch_api_bp)

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Not found"}, 404

    @app.errorhandler(500)
    def internal_error(error):
        return {"error": "Internal server error"}, 500

    return app
