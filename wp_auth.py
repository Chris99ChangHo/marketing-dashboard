# wp_auth.py: Handles logic related to WordPress user authentication.
#
# This module provides the `AuthManager` class, which is responsible for
# verifying authentication requests originating from a WordPress site.
# It processes simple authentication parameters and validates JWTs (JSON Web Tokens)
# issued by WordPress, ensuring secure access to the dashboard application.
#
# Dependencies:
# - Standard library modules: json, base64, hmac, hashlib, time, os
# - Flask (for request handling and rendering error pages)
# - python-dotenv (for loading environment variables like FLASK_SECRET_KEY)
#
# Key Classes:
# - AuthManager:
#   - __init__(): Initializes the manager with the application's secret key.
#   - _verify_wp_request(): The core method for validating WordPress authentication
#     requests, checking both simple parameters and JWT integrity and expiration.
#   - _render_error_page(): Renders a user-friendly error page for authentication failures.

import json
import base64
import hmac
import hashlib
import time
import os
from flask import request, render_template_string
from dotenv import load_dotenv

load_dotenv()

class AuthManager:
    def __init__(self):
        self.secret_key = os.getenv('FLASK_SECRET_KEY')
        if not self.secret_key:
            raise ValueError("FLASK_SECRET_KEY not found in environment variables")
        self.wordpress_auth_url = os.getenv('WORDPRESS_AUTH_URL', 'https://gnaemarketing.com.au/report/wp-admin')

    def _verify_wp_request(self):
        data_source = request.form if request.method == 'POST' else request.args

        wp_user_simple = data_source.get('wp_user')
        wp_time = data_source.get('wp_time')
        wp_auth = data_source.get('wp_auth')

        if not all([wp_user_simple, wp_time, wp_auth]):
            return None, "Missing simple authentication parameters."

        try:
            timestamp = int(wp_time)
            if time.time() - timestamp > 86400:  # 24-hour validity
                return None, "Simple auth token expired."
            
            expected_auth = hashlib.md5((wp_user_simple + wp_time + self.secret_key).encode()).hexdigest()
            if not hmac.compare_digest(wp_auth, expected_auth):
                return None, "Simple auth verification failed."
        except (ValueError, TypeError):
            return None, "Invalid simple auth timestamp."

        token = data_source.get('token')
        if not token:
            return None, "Missing token authentication parameter."

        try:
            decoded = base64.b64decode(token).decode('utf-8')
            payload, signature = decoded.split('|||')
            
            expected_signature = hmac.new(self.secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, expected_signature):
                return None, "Token signature verification failed."

            token_data = json.loads(payload)
            if time.time() > token_data.get('exp', 0):
                return None, "Token has expired."
        except (ValueError, TypeError, base64.binascii.Error, json.JSONDecodeError):
            return None, "Invalid token format."

        if wp_user_simple != token_data.get('username'):
            return None, "Authentication mismatch between simple and token auth."

        return token_data, "Authentication successful."

    def _render_error_page(self, title, message):
        template = '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>{{ title }}</title>
            <style>
                body { font-family: Arial, sans-serif; background: #f0f2f5; margin: 0; padding: 0; display: flex; align-items: center; justify-content: center; min-height: 100vh; }
                .container { background: white; padding: 40px; border-radius: 12px; text-align: center; max-width: 500px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
                .title { color: #dc3545; font-size: 28px; margin-bottom: 15px; }
                .message { color: #666; margin-bottom: 30px; line-height: 1.6; }
                .button { background: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 25px; font-weight: 600; transition: background 0.2s ease; }
                .button:hover { background: #0056b3; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="title">{{ title }}</h1>
                <p class="message">{{ message }}<br>Please try logging in again from WordPress.</p>
                <a href="{{ wordpress_auth_url }}" class="button">Go to WordPress Login</a>
            </div>
        </body>
        </html>
        '''
        return render_template_string(template, title=title, message=message, wordpress_auth_url=self.wordpress_auth_url)
