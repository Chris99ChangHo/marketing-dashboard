import os
import sys

# IMPORTANT: Set thread-related environment variables BEFORE importing numpy or other libraries.
# This prevents libraries like NumPy/OpenBLAS from spawning too many threads and hitting 
# resource limits on shared hosting environments like cPanel.
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['GOTO_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'

# Set the FLASK_ENV environment variable to 'production' for the application.
os.environ['FLASK_ENV'] = 'production'

# Add the current directory of the passenger_wsgi.py file to the Python path.
# This ensures that the 'app.py' module can be found correctly by the WSGI server.
sys.path.insert(0, os.path.dirname(__file__))

# Import the Flask application instance, named 'app', from the 'app.py' module.
# Phusion Passenger looks for a variable named 'application' by default.
from app import app as application
