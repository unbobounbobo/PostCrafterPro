"""
Local development server runner for PostCrafterPro
"""
import os
from app import create_app

# Create Flask application
app = create_app()

if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.getenv('PORT', 5000))

    # Run development server
    app.run(
        host='127.0.0.1',
        port=port,
        debug=True
    )
