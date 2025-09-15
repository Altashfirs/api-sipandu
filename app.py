import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app

# Instance aplikasi Flask
application = create_app()