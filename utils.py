# utils.py: Contains utility functions used throughout the project.
#
# This module provides a collection of general-purpose helper functions
# that are utilized across different parts of the backend application.
# These functions include image fetching and Base64 encoding, and
# interacting with the WordPress API to retrieve cover images.
#
# Dependencies:
# - requests (for making HTTP requests)
# - Standard library modules: base64, logging, datetime, threading
# - Flask (for current_app context)
#
# Key Functions:
# - get_image_base64_from_url(): Fetches an image from a given URL and returns
#   its Base64 encoded string.
# - get_default_base64_image(): Provides a small, transparent Base64 image
#   for fallback scenarios.
# - get_cover_images_from_wp(): Fetches image URLs from a specified WordPress
#   media category, used for dynamic PDF covers.

import base64
import logging
from datetime import datetime, timedelta
from threading import Lock
import json
import requests
from flask import current_app
from config import GA4_MULTI_TENANT, DEV_GA4_PROPERTY_ID, CLIENTS_REGISTRY_PATH

logger = logging.getLogger(__name__)

# --- Global Cache for WP cover images ---
PDF_COVER_IMAGE_URLS = []
LAST_COVER_FETCH_TIME = None
CACHE_LOCK = Lock()

def get_image_base64_from_url(url):
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        b64_image = base64.b64encode(response.content).decode('utf-8')
        logger.debug(f"Successfully fetched and base64 encoded image from {url}. Length: {len(b64_image)} bytes")
        return b64_image
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching image from {url}: {e}")
        return ""

def get_default_base64_image():
    # 1x1 transparent PNG
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

def get_cover_images_from_wp(category_id):
    logger.info(f"Fetching new PDF cover image URLs from WordPress for category ID: {category_id}")
    WORDPRESS_API_BASE_URL = current_app.config.get('WORDPRESS_API_BASE_URL')
    if not WORDPRESS_API_BASE_URL or not category_id:
        logger.error("WordPress API URL or Category ID is not configured.")
        return []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }
    try:
        api_url = f"{WORDPRESS_API_BASE_URL}/media?media_category={category_id}&per_page=50"
        logger.info(f"[WP API] Requesting URL: {api_url}")
        response = requests.get(api_url, headers=headers, timeout=15)
        logger.info(f"[WP API] Response Status Code: {response.status_code}")
        if not response.ok:
            logger.error(f"[WP API ERROR] Non-200 for category {category_id}. Body: {response.text}")
            return []
        media_items = response.json()
        if not media_items:
            logger.warning(f"No media items found in category {category_id}.")
            return []
        image_urls = []
        for item in media_items:
            try:
                sizes = item.get('media_details', {}).get('sizes', {})
                if 'full' in sizes:
                    url = sizes['full']['source_url']
                else:
                    url = item['source_url']
                image_urls.append(url)
            except (KeyError, TypeError):
                if item.get('source_url'):
                    image_urls.append(item.get('source_url'))
                else:
                    logger.warning(f"Could not extract valid image URL for item: {item.get('id')}")
                    continue
        https_urls = [url.replace('http://', 'https://') for url in image_urls]
        logger.info(f"Fetched and converted {len(https_urls)} image URLs to HTTPS for category {category_id}.")
        return https_urls
    except requests.exceptions.RequestException as e:
        logger.error(f"[WP API ERROR] Failed to fetch cover images: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"[WP API ERROR] Response Content: {e.response.text}")
        return []
    except Exception as e:
        logger.error(f"[WP API ERROR] Unexpected error while getting cover image list: {e}")
        return []

# --- Clients registry helpers ---

_CLIENTS_REGISTRY = None
_REGISTRY_LOAD_LOCK = Lock()

def load_clients_registry(path: str):
    """
    Loads the clients registry JSON.
    Supports:
    - dict with "clients": list
    - plain list
    - legacy dict map { "clientA": {...}, ... } -> values() used
    """
    global _CLIENTS_REGISTRY
    with _REGISTRY_LOAD_LOCK:
        if _CLIENTS_REGISTRY is None:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    _CLIENTS_REGISTRY = json.load(f)
                items = _registry_items(_CLIENTS_REGISTRY)
                logger.info(f"Clients registry loaded successfully from {path}. Found {len(items)} clients.")
            except FileNotFoundError:
                logger.error(f"Clients registry file not found at {path}.")
                _CLIENTS_REGISTRY = {}
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding clients registry JSON from {path}: {e}")
                _CLIENTS_REGISTRY = {}
            except Exception as e:
                logger.error(f"Unexpected error loading clients registry from {path}: {e}")
                _CLIENTS_REGISTRY = {}
        return _CLIENTS_REGISTRY

def _registry_items(registry):
    if isinstance(registry, dict):
        items = registry.get('clients')
        if isinstance(items, list):
            return items
        # legacy map
        return list(registry.values())
    elif isinstance(registry, list):
        return registry
    return []

def get_client_mapping(registry=None):
    """
    Returns a normalized list [{id, name, domain?, hasGA4}] for frontend.
    """
    if not GA4_MULTI_TENANT:
        logger.debug("GA4_MULTI_TENANT is false. Client mapping bypassed.")
        return []
    reg = registry or load_clients_registry(CLIENTS_REGISTRY_PATH)
    items = _registry_items(reg)
    mapping = []
    seen_ids = set()
    for c in items:
        if not isinstance(c, dict):
            continue
        cid = c.get('id')
        name = c.get('name')
        domain = c.get('domain')
        key = str(cid) if cid is not None else None
        if key is not None and key in seen_ids:
            continue
        if key is not None:
            seen_ids.add(key)
        entry = {'id': cid, 'name': name}
        if domain:
            entry['domain'] = domain
        pid = c.get('ga4_property_id') or c.get('ga4PropertyId')
        entry['hasGA4'] = bool(pid and str(pid).isdigit())
        mapping.append(entry)
    return mapping

def get_client_by_id(registry, client_id):
    cid = str(client_id)
    for c in _registry_items(registry):
        if not isinstance(c, dict):
            continue
        if str(c.get('id')) == cid:
            return c
    return None

def get_client_by_site_id(registry, site_id):
    """
    Reverse lookup: SERanking site_id -> client entry
    Supports keys: seranking_site_id, site_id, serankingSiteId
    """
    sid = str(site_id)
    for c in _registry_items(registry):
        if not isinstance(c, dict):
            continue
        value = c.get('seranking_site_id') or c.get('site_id') or c.get('serankingSiteId')
        if value is not None and str(value) == sid:
            return c
    return None

def get_ga4_property_for(registry, client_id):
    """
    Returns GA4 property ID (numeric string) for a given client_id (multi-tenant).
    Single-tenant: returns DEV_GA4_PROPERTY_ID if set and numeric.
    """
    if not GA4_MULTI_TENANT:
        logger.debug(f"GA4_MULTI_TENANT is false. Using DEV_GA4_PROPERTY_ID: {DEV_GA4_PROPERTY_ID}")
        return str(DEV_GA4_PROPERTY_ID) if DEV_GA4_PROPERTY_ID else None
    reg = registry or load_clients_registry(CLIENTS_REGISTRY_PATH)
    client = get_client_by_id(reg, client_id)
    if not client:
        logger.warning(f"Client '{client_id}' not found in registry.")
        return None
    pid = client.get('ga4_property_id') or client.get('ga4PropertyId')
    if pid and str(pid).isdigit():
        return str(pid)
    logger.warning(f"GA4 property ID missing/invalid for client '{client_id}'.")
    return None

def get_seranking_site_for(registry, client_id):
    """
    Returns SERanking site ID (string) for a given client_id (multi-tenant).
    """
    if not GA4_MULTI_TENANT:
        logger.debug("GA4_MULTI_TENANT is false. SERanking site ID mapping is bypassed.")
        return None
    reg = registry or load_clients_registry(CLIENTS_REGISTRY_PATH)
    client = get_client_by_id(reg, client_id)
    if not client:
        logger.warning(f"Client '{client_id}' not found in registry.")
        return None
    sid = client.get('seranking_site_id') or client.get('site_id') or client.get('serankingSiteId')
    return str(sid) if sid is not None else None