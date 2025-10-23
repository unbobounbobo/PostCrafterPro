"""
WSGI entry point for production deployment (PythonAnywhere)
"""
import sys
import os

# Add project directory to path
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, '.env'))

# Create application
from app import create_app
application = create_app()

if __name__ == '__main__':
    application.run()
