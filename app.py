# app.py: Main application entry point and route definitions.
#
# This file sets up the Flask application, defines API routes, and orchestrates
# data fetching from various services (Google Analytics, SE Ranking, WordPress)
# to render the marketing dashboard and generate PDF reports.
#
# Dependencies:
# - Flask, Flask-JWT-Extended, Jinja2, python-dotenv
# - Internal modules: app_factory, config, auth_service, ga4_service,
#   seranking_service, pdf_generator, wp_auth, utils
#
# Key Functions:
# - index(): Handles the main dashboard route, including authentication and rendering.
# - refresh(): Refreshes JWT access tokens.
# - logout(): Handles user logout and JWT blacklisting.
# - get_user_info(): Returns current user information.
# - get_sites_for_frontend(): Fetches client sites for the frontend.
# - get_ga4_data(): Fetches Google Analytics 4 data.
# - get_seranking_data(): Fetches SE Ranking data.
# - get_ai_summary(): Generates an AI-powered summary (internal helper).
# - get_ai_summary_route(): API endpoint for AI summary generation.
# - get_cover_images(): Fetches cover images from WordPress.
# - generate_pdf_report(): Generates the full PDF marketing report.

import os
import time
import re
import markdown
from datetime import datetime, timezone
import sqlite3

from flask import jsonify, request, make_response, render_template, current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
    set_access_cookies,
    set_refresh_cookies,
    unset_jwt_cookies,
)
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

from app_factory import create_app
from config import (
    SERANKING_API_KEY,
    FLASK_ENV,
    WORDPRESS_AUTH_URL,
    PDF_COVER_CATEGORY_ID,
    PDF_BACK_COVER_CATEGORY_ID,
    FONT_PATHS,
    GA4_MULTI_TENANT,
    DEV_GA4_PROPERTY_ID,
    CLIENTS_REGISTRY_PATH,
    WORDPRESS_API_BASE_URL,
)
from auth_service import get_google_analytics_credentials
from ga4_service import get_ga4_data_internal
import seranking_service
from pdf_generator import (
    generate_pdf_from_html,
    create_chart_image_base64,
    generate_cover_image_base64,
    generate_back_cover_image_base64,
)
from wp_auth import AuthManager
from utils import (
    get_image_base64_from_url,
    get_cover_images_from_wp,
    get_default_base64_image,
    get_client_mapping,
    get_ga4_property_for,
    get_seranking_site_for,
    load_clients_registry,
    get_client_by_site_id,
    get_client_by_id,
)

load_dotenv()
app = create_app()

# --- Production JWT Cookie Settings ---
if FLASK_ENV == 'production':
    app.config.update(
        JWT_COOKIE_SECURE=True,
        JWT_COOKIE_SAMESITE='Lax',
        JWT_COOKIE_DOMAIN=app.config.get('JWT_COOKIE_DOMAIN'),
        JWT_COOKIE_PATH='/',
        WORDPRESS_API_BASE_URL=WORDPRESS_API_BASE_URL,
    )
    app.logger.info("[JWT Config] Production settings applied.")

# --- Initializations that require app context ---
with app.app_context():
    get_google_analytics_credentials()

auth_verifier = AuthManager()

# --- Clients Registry Cache ---
CLIENTS_REGISTRY = {}
try:
    CLIENTS_REGISTRY = load_clients_registry(CLIENTS_REGISTRY_PATH)
    app.logger.info("[Registry] Clients registry loaded.")
except Exception as e:
    app.logger.warning(f"[Registry] Failed to load clients registry: {e}")
    CLIENTS_REGISTRY = {}

def read_and_display_markdown(file_name):
    try:
        file_path = os.path.join(app.root_path, file_name)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        html_style = """
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen-Sans, Ubuntu, Cantarell, "Helvetica Neue", sans-serif; line-height: 1.6; padding: 20px; max-width: 960px; margin: 20px auto; background: #f6f6f6; color: #444; }
            .container { background: #fff; padding: 40px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
            h1, h2, h3 { border-bottom: 1px solid #eaecef; padding-bottom: .3em; margin-top: 24px; margin-bottom: 16px; font-weight: 600; }
            code { background-color: #f0f0f0; padding: .2em .4em; margin: 0; font-size: 85%; border-radius: 6px; font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace; }
            pre { background-color: #f6f7f8; padding: 16px; overflow: auto; font-size: 85%; line-height: 1.45; border-radius: 6px; }
            pre code { background-color: transparent; padding: 0; margin: 0; font-size: 100%; border-radius: 0; }
            table { border-collapse: collapse; }
            th, td { border: 1px solid #dfe2e5; padding: 6px 13px; }
        </style>
        """
        html_content = markdown.markdown(content, extensions=['fenced_code', 'tables'])
        return f'''<!DOCTYPE html>
<html>
<head>
    <title>{file_name}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    {html_style}
</head>
<body>
    <div class="container">
        {html_content}
    </div>
</body>
</html>'''
    except FileNotFoundError:
        return f"<h1>Error: File not found.</h1><p>The requested file '{file_name}' was not found on the server.</p>", 404
    except Exception as e:
        app.logger.error(f"Error reading markdown file {file_name}: {e}")
        return "<h1>Server Error</h1><p>Could not read documentation.</p>", 500

def _mask_ga4_prop(prop_id):
    if not prop_id:
        return "None"
    s = str(prop_id)
    return s[:3] + "***" if len(s) > 3 else "***"

def _mask_site_id(site_id):
    s = str(site_id) if site_id is not None else "None"
    return s[:3] + "***" if len(s) > 3 else "***"

# --- Routes ---

@app.route('/', methods=['GET', 'POST'])
@jwt_required(optional=True)
def index():
    view_mode = request.args.get('view')

    # Development mode has simplified auth
    if FLASK_ENV == 'development':
        app.logger.warning("DEVELOPMENT MODE: Bypassing production authentication.")
        if view_mode == 'readme':
            return read_and_display_markdown('README.md')
        elif view_mode == 'devdocs':
            return read_and_display_markdown('Dashboard Project-documentation.md')
        fake_user_data = {'username': 'local_dev_user', 'email': 'dev@example.com', 'role': 'administrator', 'user_id': '999'}
        access_token = create_access_token(identity=fake_user_data['username'], additional_claims=fake_user_data)
        response = make_response(render_template('index.html', user_info=fake_user_data, now=int(time.time())))
        set_access_cookies(response, access_token)
        return response

    # --- Production Authentication Logic ---
    current_user_identity = get_jwt_identity()
    if current_user_identity:
        if view_mode == 'readme':
            return read_and_display_markdown('README.md')
        elif view_mode == 'devdocs':
            return read_and_display_markdown('Dashboard Project-documentation.md')
        else:
            return render_template('index.html', user_info=get_jwt(), now=int(time.time()))

    user_data, message = auth_verifier._verify_wp_request()
    if user_data:
        username = str(user_data.get('username', ''))
        if not username:
            return auth_verifier._render_error_page("Authentication Failed", "Username is missing in user data."), 401
        RESERVED_CLAIMS = {"sub", "exp", "iat", "nbf", "jti", "aud", "iss"}
        custom_claims = {k: v for k, v in user_data.items() if k not in RESERVED_CLAIMS}
        access_token = create_access_token(identity=username, additional_claims=custom_claims)
        refresh_token = create_refresh_token(identity=username, additional_claims=custom_claims)
        if view_mode == 'readme':
            response = make_response(read_and_display_markdown('README.md'))
        elif view_mode == 'devdocs':
            response = make_response(read_and_display_markdown('Dashboard Project-documentation.md'))
        else:
            response = make_response(render_template('index.html', user_info=user_data, now=int(time.time())))
        set_access_cookies(response, access_token)
        set_refresh_cookies(response, refresh_token)
        return response

    return auth_verifier._render_error_page("Authentication Required", "Please log in through WordPress to access this page."), 401

@app.route('/api/token/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    claims = get_jwt()
    RESERVED_CLAIMS = {"sub", "exp", "iat", "nbf", "jti", "aud", "iss", "type"}
    custom_claims = {k: v for k, v in claims.items() if k not in RESERVED_CLAIMS}
    access_token = create_access_token(identity=identity, additional_claims=custom_claims)
    response = jsonify({'status': 'success', 'message': 'Token refreshed successfully'})
    set_access_cookies(response, access_token)
    return response

@app.route('/api/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()['jti']
    expires_at = datetime.fromtimestamp(get_jwt()['exp'], tz=timezone.utc)
    blacklist_db_path = os.path.join(current_app.instance_path, 'data', 'blacklist.db')
    try:
        os.makedirs(os.path.dirname(blacklist_db_path), exist_ok=True)
        conn = sqlite3.connect(blacklist_db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS token_blacklist (jti TEXT PRIMARY KEY, expires_at TEXT)")
        cursor.execute("INSERT OR REPLACE INTO token_blacklist (jti, expires_at) VALUES (?, ?)", (jti, str(expires_at)))
        conn.commit()
        conn.close()
    except Exception as e:
        current_app.logger.error(f"Failed to add token to blacklist: {e}")

    response = jsonify({'message': 'Successfully logged out', 'redirect': WORDPRESS_AUTH_URL})
    unset_jwt_cookies(response)
    return response

@app.route('/api/user-info', methods=['GET'])
@jwt_required()
def get_user_info():
    import json
    current_user = get_jwt_identity()
    claims = get_jwt()
    if FLASK_ENV == 'development':
        app.logger.debug(f"[API] get_user_info - current_user: {current_user}, claims: {claims}")
    response_data = {
        'username': current_user,
        'email': claims.get('email'),
        'role': claims.get('role'),
        'user_id': claims.get('user_id'),
        'token_expires_at': claims.get('exp'),
    }
    return make_response(json.dumps(response_data), 200, {'Content-Type': 'application/json'})

@app.route('/api/sites', methods=['GET'])
@jwt_required()
def get_sites_for_frontend():
    if GA4_MULTI_TENANT:
        try:
            mapping = get_client_mapping(CLIENTS_REGISTRY)
            clients = [{'id': c.get('id'), 'name': c.get('name')} for c in mapping]
            return jsonify({'status': 'success', 'clients': clients})
        except Exception as e:
            current_app.logger.error(f"[Sites] Failed to build sites from registry: {e}")
            return jsonify({'status': 'error', 'message': 'Failed to load clients from registry'}), 500
    else:
        return jsonify(seranking_service.get_clients_for_frontend())

@app.route('/api/ga4_data', methods=['GET'])
@jwt_required()
def get_ga4_data():
    client_id = request.args.get('client_id')
    site_id = request.args.get('site_id')
    start_date_str = request.args.get('start_date', '7daysAgo')
    end_date_str = request.args.get('end_date', 'today')

    if GA4_MULTI_TENANT:
        # client_id가 없고 site_id가 있으면 역조회
        if not client_id and site_id:
            client_entry = get_client_by_site_id(CLIENTS_REGISTRY, site_id)
            if client_entry:
                client_id = client_entry.get('id')
        if not client_id:
            return jsonify({'error': 'client_id or site_id is required in multi-tenant mode'}), 400

        resolved_property = get_ga4_property_for(CLIENTS_REGISTRY, client_id)
        if not resolved_property:
            # GA4 미연결: GA4 섹션 비활성화를 위해 204 반환(본문 없음)
            return ("", 204)
        if not str(resolved_property).isdigit():
            return jsonify({'error': f'GA4 property must be numeric, got {resolved_property}'}), 400
    else:
        resolved_property = DEV_GA4_PROPERTY_ID
        if not resolved_property or not str(resolved_property).isdigit():
            return jsonify({'error': 'DEV_GA4_PROPERTY_ID is not set or invalid'}), 500

    if FLASK_ENV == 'development':
        app.logger.debug(f"[GA4] resolved_property(raw)={resolved_property!r}, client_id={client_id}, site_id={site_id}")

        ga4_data = get_ga4_data_internal(resolved_property, start_date_str, end_date_str)
    return jsonify(ga4_data)

@app.route('/api/seranking_data', methods=['GET'])
@jwt_required()
def get_seranking_data():
    client_id = request.args.get('client_id')
    site_id = request.args.get('site_id')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    if GA4_MULTI_TENANT:
        if client_id:
            resolved_site = get_seranking_site_for(CLIENTS_REGISTRY, client_id)
            if not resolved_site and not site_id:
                app.logger.info(f"[SER] Missing mapping for client_id='{client_id}'")
                return jsonify({'error': 'Client is not configured for SERanking', 'client_id': client_id}), 400
            site_id = site_id or resolved_site
        elif not site_id:
            return jsonify({'error': 'Either client_id or site_id is required'}), 400

    if FLASK_ENV == 'development':
        app.logger.debug(f"[SER] client_id='{client_id}', site_id='****'")

    seranking_data = seranking_service.get_seranking_data_internal(site_id, start_date_str, end_date_str)
    return jsonify(seranking_data)

def get_ai_summary(ga4_data, seranking_data, client_name, report_period):
    from openai import OpenAI
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        base_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.join(base_dir, 'etc', 'prompt-eng.txt')
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()

        prompt = prompt_template.format(
            Date_Range=report_period,
            Client_Name=client_name,
            Total_Sessions=ga4_data.get('total_sessions', 'N/A'),
            Total_Users=ga4_data.get('total_users', 'N/A'),
            Avg_Engagement_Time=f"{ga4_data.get('average_engagement_time', 0):.2f}s",
            New_Users=ga4_data.get('new_users', 'N/A'),
            Bounce_Rate=f"{(1 - ga4_data.get('engagement_rate', 0)) * 100:.2f}%",
            Mobile_Users_Percent=f"{ga4_data.get('device_users', {}).get('mobile_percent', 0):.2f}%",
            Desktop_Users_Percent=f"{ga4_data.get('device_users', {}).get('desktop_percent', 0):.2f}%",
            Search_Traffic=ga4_data.get('traffic_by_type', {}).get('search', 'N/A'),
            Direct_Traffic=ga4_data.get('traffic_by_type', {}).get('direct', 'N/A'),
            Avg_Top10_Keyword_Rank=seranking_data.get('avg_top_10_rank', 'N/A'),
            Keywords_Up=seranking_data.get('ranking_change_distribution', {}).get('up', 0),
            Keywords_Down=seranking_data.get('ranking_change_distribution', {}).get('down', 0),
            New_Top100_Keywords=len(seranking_data.get('top_100_new_entries', [])),
            Visibility_Drop_Keywords=len(seranking_data.get('top_100_disappeared', [])),
        )

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional marketing analyst."},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        app.logger.error(f"Error getting AI summary: {e}")
        return "Error generating AI summary."

@app.route('/api/ai_summary', methods=['POST'])
@jwt_required()
def get_ai_summary_route():
    data = request.json
    ga4_data = data.get('ga4_data', {})
    seranking_data = data.get('seranking_data', {})
    client_name = data.get('client_name', 'N/A')
    report_period = seranking_data.get('report_period', 'N/A')

    summary = get_ai_summary(ga4_data, seranking_data, client_name, report_period)
    return jsonify({"summary": summary})

@app.route('/api/cover-images', methods=['GET'])
@jwt_required()
def get_cover_images():
    category_type = request.args.get('category', 'front')
    category_id = PDF_BACK_COVER_CATEGORY_ID if category_type == 'back' else PDF_COVER_CATEGORY_ID
    image_urls = get_cover_images_from_wp(category_id)
    return jsonify({"image_urls": image_urls})

@app.route('/generate-pdf-report', methods=['POST'])
@jwt_required()
def generate_pdf_report():
    data = request.json
    client_id = data.get('client_id')
    site_id = data.get('site_id')
    start_date_str = data.get('startDate', '7daysAgo')
    end_date_str = data.get('endDate', 'today')

    reg = load_clients_registry(CLIENTS_REGISTRY_PATH)

    # client_id 없고 site_id만 있으면 역조회
    if GA4_MULTI_TENANT and not client_id and site_id:
        entry = get_client_by_site_id(reg, site_id)
        if entry:
            client_id = entry.get('id')

    ga4_prop = None
    ser_site = None
    if GA4_MULTI_TENANT and client_id:
        ga4_prop = get_ga4_property_for(reg, client_id)
        ser_site = get_seranking_site_for(reg, client_id)

    # SERanking clients에서 selected_client 찾기
    selected_client = None
    all_clients_response = seranking_service.get_clients_for_frontend()
    if all_clients_response and all_clients_response.get('status') == 'success':
        all_clients = all_clients_response.get('clients', [])
        target_id = ser_site or site_id or client_id
        for client in all_clients:
            if str(client.get('id')) == str(target_id):
                selected_client = client
                break

    # SERanking에서 못 찾으면 레지스트리 최소 정보로 구성
    if not selected_client:
        entry = get_client_by_id(reg, client_id) if client_id else None
        if entry:
            selected_client = {
                "id": ser_site or site_id or client_id,
                "name": entry.get("name", str(client_id or site_id)),
                "domain": entry.get("domain")
            }
        else:
            return jsonify({"error": f"Client '{client_id or site_id}' not found."}), 404

    ga4_property_id_for_report = ga4_prop or DEV_GA4_PROPERTY_ID
    seranking_site_id_for_report = ser_site or site_id or selected_client.get('id')

    app.logger.info(f"[PDF] client_id='{client_id}', GA4='{_mask_ga4_prop(ga4_property_id_for_report)}', SER='{_mask_site_id(seranking_site_id_for_report)}'")

    # GA4 호출: 미연결이면 빈 데이터로 대체
    ga4_data = {}
    try:
        if ga4_property_id_for_report and str(ga4_property_id_for_report).isdigit():
            ga4_data = get_ga4_data_internal(ga4_property_id_for_report, start_date_str, end_date_str)
    except Exception as e:
        app.logger.warning(f"[PDF] GA4 fetch failed, continue with SERanking only: {e}")
        ga4_data = {}

    ga4_previous_data = ga4_data.get('previous_period_data', {})

    seranking_data_from_frontend = data.get('seranking_data', {})
    # AI Summary
    ai_summary = get_ai_summary(
        ga4_data,
        seranking_data_from_frontend,
        selected_client.get('name'),
        seranking_data_from_frontend.get('report_period'),
    )

    # Prepare SERanking data for rendering
    final_seranking_data = {
        "keyword_rankings": seranking_data_from_frontend.get("keyword_rankings", []),
        "top_100_new_entries": seranking_data_from_frontend.get("top_100_new_entries", []),
        "top_100_disappeared": seranking_data_from_frontend.get("top_100_disappeared", []),
        "ranking_change_distribution": seranking_data_from_frontend.get("ranking_change_distribution", {}),
        "report_period": seranking_data_from_frontend.get("report_period", ""),
        "segment_summary": seranking_data_from_frontend.get("segment_summary", {}),
        "report_period_month_year": seranking_data_from_frontend.get("report_period_month_year", "Monthly Report"),
    }

    # Compute rank change display fields
    for kw in final_seranking_data["keyword_rankings"]:
        try:
            prev_rank_match = re.search(r'^(\d+)', str(kw.get("previous_rank")))
            curr_rank_match = re.search(r'^(\d+)', str(kw.get("current_rank")))
            prev_rank_int = int(prev_rank_match.group(1)) if prev_rank_match else None
            curr_rank_int = int(curr_rank_match.group(1)) if curr_rank_match else None
        except (ValueError, AttributeError):
            prev_rank_int, curr_rank_int = None, None

        if prev_rank_int is None or curr_rank_int is None:
            kw["change_class"], kw["change_display"] = "change-na", "N/A"
        elif prev_rank_int == curr_rank_int:
            kw["change_class"], kw["change_display"] = "change-same", "-"
        elif curr_rank_int < prev_rank_int:
            kw["change_class"], kw["change_display"] = "change-up", f"▲ {prev_rank_int - curr_rank_int}"
        else:
            kw["change_class"], kw["change_display"] = "change-down", f"▼ {curr_rank_int - prev_rank_int}"

    # --- Image Data Preparation ---
    cover_logo_base64 = get_image_base64_from_url("https://gnasolutions.com.au/wp-content/uploads/2024/07/logo-2024.png")
    seo_intro_image_base64 = get_image_base64_from_url("https://gnaemarketing.com.au/report/wp-content/uploads/2019/12/ranking.jpg")
    ser_ranking_image_base64 = get_image_base64_from_url("https://gnaemarketing.com.au/report/wp-content/uploads/2019/12/segment.jpg")

    front_cover_url = data.get('front_cover_image_url')
    back_cover_url = data.get('back_cover_image_url')

    app.logger.debug(f"Received front cover URL: {front_cover_url}")
    app.logger.debug(f"Received back cover URL: {back_cover_url}")

    front_cover_base64 = get_image_base64_from_url(front_cover_url) if front_cover_url else get_default_base64_image()
    back_cover_base64 = get_image_base64_from_url(back_cover_url) if back_cover_url else get_default_base64_image()

    # --- Generate Cover Images with Text ---
    final_front_cover_base64 = generate_cover_image_base64(
        base_image_base64=front_cover_base64,
        client_name=selected_client.get('name'),
        report_title="ONLINE MARKETING MONTHLY REPORT",
        domain=selected_client.get('domain'),
        period=final_seranking_data.get('report_period_month_year'),
    )

    contact_details = "Suite 602, 6 Help Street Chatswood, NSW 2067\n+61 2 9299 5959 / 425 835 246\nletustalk@gnasolutions.com.au\nMonday - Friday (except public holidays)"
    final_back_cover_base64 = generate_back_cover_image_base64(
        base_image_base64=back_cover_base64,
        contact_info=contact_details,
    )

    # --- Chart Image Generation ---
    page_views_chart_base64 = create_chart_image_base64(
        current_data={'Total Page Views': ga4_data.get('total_page_views', 0), 'Page / Visit': ga4_data.get('page_per_visit', 0)},
        previous_data={'Total Page Views': ga4_previous_data.get('total_page_views', 0), 'Page / Visit': ga4_previous_data.get('page_per_visit', 0)},
        chart_type='comparison_bar', title='Page Views Comparison', y_label='Amount',
    )
    device_users_chart_base64 = create_chart_image_base64(
        current_data=ga4_data.get('device_users', {}),
        previous_data=ga4_data.get('last_month_device_users', {}),
        chart_type='comparison_bar', title='Device Users Comparison', y_label='Users',
    )
    traffic_source_chart_base64 = create_chart_image_base64(
        current_data=ga4_data.get('traffic_by_type', {}),
        chart_type='donut', title='Traffic Sources Distribution', show_percentage=True,
    )

    # --- Render HTML for PDF ---
    # 주의: Passenger 환경에서 상대경로 이슈가 있으면 절대경로로 교체
    # base_dir = os.path.dirname(os.path.abspath(__file__))
    # template_loader = FileSystemLoader(searchpath=os.path.join(base_dir, "templates"))
    template_loader = FileSystemLoader(searchpath="./templates")
    template_env = Environment(loader=template_loader)
    template = template_env.get_template('report_full_document.html')

    template_context = {
        "ga4_data": ga4_data,
        "seranking_data": final_seranking_data,
        "selected_client": selected_client,
        "ai_summary": ai_summary,
        "report_period_month_year": final_seranking_data.get('report_period_month_year'),
        "page_views_chart_base64": page_views_chart_base64,
        "device_users_chart_base64": device_users_chart_base64,
        "traffic_source_chart_base64": traffic_source_chart_base64,
        "cover_logo_base64": cover_logo_base64,
        "seo_intro_image_base64": seo_intro_image_base64,
        "ser_ranking_image_base64": ser_ranking_image_base64,
        "front_cover_image_base64": final_front_cover_base64 or front_cover_base64,
        "back_cover_image_base64": final_back_cover_base64 or back_cover_base64,
        "font_paths": FONT_PATHS,
    }

    rendered_html = template.render(template_context)

    # Remove bold tags to prevent font rendering issues when bold font files are not available
    rendered_html = rendered_html.replace("<strong>", "").replace("</strong>", "")
    rendered_html = rendered_html.replace("<b>", "").replace("</b>", "")

    pdf_bytes = generate_pdf_from_html(rendered_html)
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=marketing_report.pdf'
    return response

if __name__ == '__main__':
    # 개발시만 debug True
    app.run(debug=(FLASK_ENV == 'development'), host='0.0.0.0', port=5001)