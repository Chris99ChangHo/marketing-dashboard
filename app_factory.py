# app_factory.py: Implements the factory pattern for creating the Flask application instance.
#
# This file defines the `create_app` function, which is responsible for initializing
# and configuring the Flask application. This pattern allows for flexible application
# setup, especially useful for testing and managing different environments (development, production).
# It also sets up JWT (JSON Web Token) management, database for token blacklisting,
# and logging configurations.
#
# Dependencies:
# - Flask, Flask-CORS, Flask-JWT-Extended, Flask-Limiter
# - Standard library modules: logging, os, pathlib, sqlite3, datetime
# - Internal modules: config
#
# Key Functions:
# - create_app(): The main factory function that returns a configured Flask app instance.
#   - Configures Flask settings (secret keys, JWT parameters).
#   - Initializes Flask extensions (JWTManager, Limiter).
#   - Sets up the SQLite database for JWT token blacklisting.
#   - Defines JWT error handlers (expired, invalid, unauthorized, revoked tokens).
#   - Configures application logging to console and file.

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import sqlite3
from datetime import datetime, timezone, timedelta

from flask import Flask, config, jsonify, render_template_string, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import config

def create_app():
    """Creates and configures the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    # --- App Configuration ---
    app.config.from_mapping(
        SECRET_KEY=config.FLASK_SECRET_KEY,
        JWT_SECRET_KEY=config.JWT_SECRET_KEY,
        JWT_TOKEN_LOCATION=["cookies"],
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(minutes=30),
        JWT_REFRESH_TOKEN_EXPIRES=timedelta(days=30),
        JWT_COOKIE_HTTPONLY=True,
        JWT_CSRF_COOKIE_HTTPONLY=False,
        JWT_COOKIE_SAMESITE="Lax", # Strict is too restrictive for some browsers
        JWT_ACCESS_COOKIE_PATH="/",
        JWT_REFRESH_COOKIE_PATH="/",
        WORDPRESS_API_BASE_URL=config.WORDPRESS_API_BASE_URL,
        PDF_COVER_CATEGORY_ID=config.PDF_COVER_CATEGORY_ID
    )

    if config.FLASK_ENV == 'development':
        app.config.update(
            JWT_COOKIE_CSRF_PROTECT=False,
            JWT_COOKIE_SECURE=False,
            JWT_ACCESS_TOKEN_EXPIRES=timedelta(days=30)
        )
    else:
        app.config.update(
            JWT_COOKIE_CSRF_PROTECT=True,
            JWT_COOKIE_SECURE=True
        )

    # --- Ensure instance folder exists ---
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # --- Initialize Extensions ---
    jwt = JWTManager(app)
    Limiter(
        get_remote_address,
        app=app,
        storage_uri="memory://",
        default_limits=["200 per day", "50 per hour"]
    )

    # --- Database Setup ---
    blacklist_db_path = os.path.join(app.instance_path, 'data', 'blacklist.db')
    os.makedirs(os.path.dirname(blacklist_db_path), exist_ok=True)

    def setup_database():
        try:
            conn = sqlite3.connect(blacklist_db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS token_blacklist (
                    jti TEXT PRIMARY KEY,
                    expires_at TIMESTAMP NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_jti ON token_blacklist (jti)")
            conn.commit()
            conn.close()
        except Exception as e:
            app.logger.error(f"Failed to initialize SQLite blacklist database: {e}")

    with app.app_context():
        setup_database()

    # --- JWT Error Handlers ---
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        app.logger.error(f"--- JWT EXPIRED --- Path: {request.path}")
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Token has expired', 'code': 'TOKEN_EXPIRED', 'refresh_required': True}), 401
        else:
            return render_template_string("Session Expired. Please login again."), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        app.logger.error(f"--- JWT INVALID --- Path: {request.path}, Error: {error}")
        return jsonify({'error': 'Invalid token', 'code': 'INVALID_TOKEN'}), 401

    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        app.logger.error(f"--- JWT UNAUTHORIZED --- Path: {request.path}, Error: {error}")
        return jsonify({'error': 'Token required', 'code': 'TOKEN_REQUIRED'}), 401

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload['jti']
        try:
            conn = sqlite3.connect(blacklist_db_path)
            cursor = conn.cursor()
            current_time = datetime.now(timezone.utc)
            cursor.execute("SELECT EXISTS(SELECT 1 FROM token_blacklist WHERE jti=? AND expires_at > ?)", (jti, current_time.isoformat()))
            is_revoked = cursor.fetchone()[0]
            conn.close()
            return is_revoked
        except Exception as e:
            app.logger.error(f"Blacklist DB check failed: {e}")
            return True

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': 'Token has been revoked', 'code': 'TOKEN_REVOKED'}), 401

    # --- Logging Setup (Always active for debugging) ---
    # Clear existing handlers to prevent duplicate logs
    if app.logger.handlers:
        app.logger.handlers.clear()
    if logging.getLogger().handlers: # Also clear root logger handlers
        logging.getLogger().handlers.clear()

    # Set root logger level to DEBUG to capture all messages
    logging.getLogger().setLevel(logging.DEBUG)
    app.logger.setLevel(logging.DEBUG)

    # Console handler (for local development visibility)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.addHandler(stream_handler)

    # File handler (for persistent logs, especially on servers)
    log_file_path = os.path.join(app.instance_path, 'error.log') # Ensure log file is in instance folder
    file_handler = RotatingFileHandler(log_file_path, maxBytes=1024 * 1024 * 10, backupCount=10)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.DEBUG) # Ensure DEBUG messages are written to file
    app.logger.addHandler(file_handler)

    if config.FLASK_ENV == 'development':
        app.logger.debug(f"DEBUG: app.instance_path is: {app.instance_path}") # Log instance path

    # Explicitly set seranking_service logger to DEBUG
    logging.getLogger('seranking_service').setLevel(logging.DEBUG)
    logging.getLogger('utils').setLevel(logging.DEBUG) # Also set utils logger for image debugging

    return app
