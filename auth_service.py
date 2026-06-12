# auth_service.py: Handles Google Analytics authentication-related logic.
#
# This module is responsible for managing the authentication credentials
# required to access the Google Analytics Data API (GA4). It handles
# loading existing credentials, refreshing them when expired, and initiating
# the OAuth 2.0 flow to create new credentials if necessary.
#
# Dependencies:
# - google.oauth2.credentials, google.auth.transport.requests,
#   google_auth_oauthlib.flow
# - Standard library modules: os, json, logging
# - Internal modules: config
#
# Key Functions:
# - get_google_analytics_credentials(): Orchestrates the entire credential
#   management process, ensuring valid credentials are available.
# - get_global_credentials(): Provides access to the globally stored
#   Google Analytics credentials for other modules.

import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import json
import logging

# Import settings from config.py
from config import CLIENT_SECRET_FILE, CREDENTIALS_FILE, SCOPES

# Configure logger (reuse logger from app.py or set up separately)
logger = logging.getLogger(__name__)
if not logger.handlers:
    # Logger is configured in app.py, so no handlers are added here.
    # If needed, a StreamHandler etc. can be added here.
    pass

global_credentials = None

def get_google_analytics_credentials():
    """
    Retrieves user authentication credentials for accessing the Google Analytics API.
    It loads existing credentials, refreshes them if expired, or creates new ones if they don't exist.
    """
    global global_credentials
    creds = None

    if os.path.exists(CREDENTIALS_FILE):
        try:
            creds = Credentials.from_authorized_user_file(CREDENTIALS_FILE, SCOPES)
            logger.debug("Successfully authenticated with existing credentials.json file.")
        except Exception as e:
            logger.debug(f"The credentials.json file is invalid. Attempting re-authentication. Error: {e}")
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.debug("The credentials.json file has expired. Attempting to refresh.")
            try:
                creds.refresh(Request())
                logger.debug("Successfully refreshed credentials.json file.")
            except Exception as e:
                logger.debug(f"Failed to refresh credentials.json file. Attempting re-authentication. Error: {e}")
                creds = None
        
        if not creds:
            logger.debug("Attempting to create and authenticate a new credentials.json file.")
            if not os.path.exists(CLIENT_SECRET_FILE):
                logger.error(f"client_secret.json file not found: {CLIENT_SECRET_FILE}")
                return None
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CLIENT_SECRET_FILE, SCOPES
                )
                creds = flow.run_local_server(port=0)
                
                with open(CREDENTIALS_FILE, 'w') as token:
                    token.write(creds.to_json())
                logger.debug("Successfully created and authenticated a new credentials.json file.")
            except Exception as e:
                logger.error(f"An error occurred during Google Analytics authentication: {e}")
                creds = None

    global_credentials = creds
    return creds

def get_global_credentials():
    """
    Returns the currently stored global Google Analytics credentials.
    """
    return global_credentials
