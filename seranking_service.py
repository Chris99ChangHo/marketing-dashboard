# seranking_service.py: Handles logic related to the SERanking API.
#
# This module is responsible for fetching keyword ranking data and client (site)
# information from the SERanking API. It processes the raw API responses
# into a structured format suitable for display on the dashboard and PDF reports.
# It also handles API authentication and error management specific to SERanking.
#
# Dependencies:
# - requests (for making HTTP requests to the SERanking API)
# - Standard library modules: logging, datetime
# - Internal modules: config (for SERanking API key and base URL)
#
# Key Functions:
# - get_seranking_sites_from_api(): Fetches the list of registered projects/sites
#   from the SERanking account.
# - get_seranking_data_internal(site_id, start_date_str, end_date_str):
#   Retrieves detailed keyword ranking data for a specific site and date range,
#   including ranking changes, new/disappeared keywords, and segment summaries.
# - get_clients_for_frontend(): Prepares and returns a list of clients suitable
#   for display on the frontend, integrating SERanking site data.

import requests
from requests.exceptions import RequestException
import logging
from datetime import date, timedelta, datetime
from config import SERANKING_API_KEY, SERANKING_BASE_URL

logger = logging.getLogger(__name__)
logger.debug("DEBUG: seranking_service.py module loaded.")  # Added module load log


def get_seranking_sites_from_api():
    """
    Fetches the list of registered projects/sites from the SERanking account.
    """
    logger.debug("DEBUG: get_seranking_sites_from_api function called.")

    if not SERANKING_API_KEY:
        logger.error("SERANKING_API_KEY is not set. Cannot call SERanking API.")
        return None

    headers = {
        'Authorization': f'Token {SERANKING_API_KEY}',
        'Accept': 'application/json',
    }

    url = f"{SERANKING_BASE_URL}/sites"
    logger.debug(f"Attempting SERanking API call: {url}")
    logger.debug(f"Request Headers: {headers}")

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        sites = []
        if isinstance(data, dict) and "items" in data and isinstance(data["items"], list):
            sites = data["items"]
        elif isinstance(data, list):
            sites = data
        else:
            logger.warning(f"SERanking project list response structure is unexpected. Original response: {data}")
            sites = []

        for site in sites:
            logger.debug(f"DEBUG: Raw SERanking site data: {site}")
            if 'name' not in site or site['name'] is None:
                logger.warning(f"SERanking site ID {site.get('id', 'N/A')} is missing or has a None 'name' field.")

        logger.info(f"Successfully fetched {len(sites)} SERanking projects.")
        return sites

    except RequestException as e:
        response_text = getattr(e.response, 'text', 'N/A')
        logger.error(f"SERanking API call failed: {e}. Response body: {response_text}")
        if e.response and e.response.status_code == 400:
            logger.error("400 Bad Request: API key might be invalid, or endpoint/parameters might be incorrect.")
        return None
    except Exception as e:
        logger.error(f"Error processing SERanking API response: {e}")
        return None


def get_seranking_data_internal(site_id, start_date_str, end_date_str):
    """
    Retrieves detailed keyword ranking data for a specific site and date range.
    """
    logger.debug(f"DEBUG: Entering get_seranking_data_internal with site_id={site_id}, start_date={start_date_str}, end_date={end_date_str}")  # Added entry log
    logger.debug(f"DEBUG: _get_seranking_data_internal called. start_date_str='{start_date_str}', end_date_str='{end_date_str}'")

    if not SERANKING_API_KEY:
        logger.error("SERANKING_API_KEY is not set. Cannot process SERanking data request.")
        raise Exception("SERanking API key is not configured.")

    if not site_id or not str(site_id).isdigit():
        logger.warning(f"SERanking API: Invalid site_id: {site_id}")
        raise ValueError("A valid SERanking Site ID was not provided.")

    try:
        if not start_date_str or start_date_str == '7daysAgo':
            start_date_obj = date.today() - timedelta(days=6)
            logger.debug(f"DEBUG: start_date not provided, set to default: {start_date_obj}")
        else:
            start_date_obj = datetime.strptime(start_date_str, '%Y-%m-%d').date()

        if not end_date_str or end_date_str == 'today':
            end_date_obj = date.today()
            logger.debug(f"DEBUG: end_date not provided, set to default: {end_date_obj}")
        else:
            end_date_obj = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    except ValueError as e:
        logger.error(f"SERanking API: Date format error: {e}")
        raise ValueError("Invalid date format. Please use YYYY-MM-DD.")

    headers = {
        "Accept": "application/json",
        "Authorization": f"Token {SERANKING_API_KEY}",
        "Content-Type": "application/json; charset=utf-8"
    }

    params = {
        "date_from": start_date_obj.strftime('%Y-%m-%d'),
        "date_to": end_date_obj.strftime('%Y-%m-%d'),
        "with_serp_features": "1"
    }

    fetch_url = f"{SERANKING_BASE_URL}/sites/{site_id}/positions"
    logger.debug(f"Attempting SERanking API call: {fetch_url} (params: {params})")

    response = requests.get(fetch_url, headers=headers, params=params, timeout=10)
    response.raise_for_status()
    logger.debug(f"DEBUG: SERanking API response status for positions: {response.status_code}")  # Added debug log for status code
    seranking_raw_data = response.json()
    logger.debug(f"DEBUG: Raw SERanking API response for positions: {seranking_raw_data}")  # Added debug log for raw response

    keyword_rankings = []
    items_to_process = []
    if isinstance(seranking_raw_data, dict) and "items" in seranking_raw_data and isinstance(seranking_raw_data["items"], list):
        items_to_process = seranking_raw_data["items"]
    elif isinstance(seranking_raw_data, list):
        items_to_process = seranking_raw_data
    else:
        logger.warning(f"SERanking keyword ranking response structure is unexpected. Original response: {seranking_raw_data}")

    logger.debug(f"DEBUG: Items to process for keywords: {items_to_process}")  # Added log for items_to_process

    ranking_change_distribution = {"up": 0, "down": 0, "unchanged": 0, "new": 0}
    top_100_new_entries = []
    top_100_disappeared = []
    overall_rank_distribution = {"top_1_10": 0, "top_11_20": 0, "top_21_50": 0, "top_51_100": 0}

    for item_data in items_to_process:
        keywords_list = item_data.get('keywords', [])

        for kw in keywords_list:
            name = kw.get('name', 'N/A')
            logger.debug(f"DEBUG: Processing keyword name: '{name}'")  # Added debug log
            positions = kw.get('positions', [])

            firstp = 0
            lastp = 0

            for po in positions:
                if po.get('date') == start_date_obj.strftime('%Y-%m-%d'):
                    firstp = po.get('pos', 0)
                if po.get('date') == end_date_obj.strftime('%Y-%m-%d'):
                    lastp = po.get('pos', 0)

            fval = firstp if firstp != 0 else 100
            lval = lastp if lastp != 0 else 100

            if firstp == 0 and lastp > 0:
                ranking_change_distribution["new"] += 1
                if lastp <= 100:
                    top_100_new_entries.append({"keyword": name, "rank": lastp})
            elif lastp == 0 and firstp > 0:
                top_100_disappeared.append({"keyword": name, "rank": firstp})
            elif firstp > 0 and lastp > 0:
                if lastp < firstp:
                    ranking_change_distribution["up"] += 1
                elif lastp > firstp:
                    ranking_change_distribution["down"] += 1
                else:
                    ranking_change_distribution["unchanged"] += 1

            if 1 <= lastp <= 10:
                overall_rank_distribution["top_1_10"] += 1
            elif 11 <= lastp <= 20:
                overall_rank_distribution["top_11_20"] += 1
            elif 21 <= lastp <= 50:
                overall_rank_distribution["top_21_50"] += 1
            elif 51 <= lastp <= 100:
                overall_rank_distribution["top_51_100"] += 1

            firstp_display = str(firstp) if firstp != 0 else 'NA'
            lastp_display = str(lastp) if lastp != 0 else 'NA'

            def get_rank_category(rank_val):
                if rank_val == 0:
                    return '<span>-</span>'
                elif rank_val < 6:
                    return '<span style="color:#2585c9;">R1</span>'
                elif rank_val < 11:
                    return '<span style="color:#06b254;">R2</span>'
                elif rank_val < 21:
                    return '<span style="color:#ffc207;">R3</span>'
                elif rank_val < 41:
                    return '<span style="color:#7131a1;">R4</span>'
                else:
                    return '<span style="color:#ff4242;">R5</span>'

            firstps_html = get_rank_category(firstp)
            lastps_html = get_rank_category(lastp)

            change_val = lval - fval
            change_class = ""
            change_display = ""

            if firstp == 0 and lastp > 0:
                change_class = "new"
                change_display = f"New"
            elif lastp == 0 and firstp > 0:
                change_class = "dropped"
                change_display = f"Out"
            elif change_val < 0:
                change_class = "up"
                change_display = f"▲ {abs(change_val)}"
            elif change_val > 0:
                change_class = "rank-down"
                change_display = f"▼ {change_val}"
            else:
                change_class = "unchanged"
                change_display = "-"

            keyword_rankings.append({
                "keyword": name,
                "previous_rank": f"{firstp_display}/{firstps_html}",
                "current_rank": f"{lastp_display}/{lastps_html}",
                "change_class": change_class,
                "change_display": change_display
            })

    report_period_message = f"Report from {start_date_obj.strftime('%Y-%m-%d')} to {end_date_obj.strftime('%Y-%m-%d')}"
    report_period_month_year = end_date_obj.strftime('%B %Y')  # e.g., "July 2025"

    segment_summary = {f'R{i}': {'previous_month': 0, 'current_month': 0} for i in range(1, 6)}

    for kw_entry in keyword_rankings:
        prev_rank_str = kw_entry['previous_rank'].split('/')[0]
        curr_rank_str = kw_entry['current_rank'].split('/')[0]

        prev_rank_val = int(prev_rank_str) if prev_rank_str.isdigit() else 0
        curr_rank_val = int(curr_rank_str) if curr_rank_str.isdigit() else 0

        if 1 <= curr_rank_val <= 5:
            segment_summary['R1']['current_month'] += 1
        elif 6 <= curr_rank_val <= 10:
            segment_summary['R2']['current_month'] += 1
        elif 11 <= curr_rank_val <= 20:
            segment_summary['R3']['current_month'] += 1
        elif 21 <= curr_rank_val <= 40:
            segment_summary['R4']['current_month'] += 1
        elif curr_rank_val >= 41 and curr_rank_val <= 100:
            segment_summary['R5']['current_month'] += 1

        if 1 <= prev_rank_val <= 5:
            segment_summary['R1']['previous_month'] += 1
        elif 6 <= prev_rank_val <= 10:
            segment_summary['R2']['previous_month'] += 1
        elif 11 <= prev_rank_val <= 20:
            segment_summary['R3']['previous_month'] += 1
        elif 21 <= prev_rank_val <= 40:
            segment_summary['R4']['previous_month'] += 1
        elif prev_rank_val >= 41 and prev_rank_val <= 100:
            segment_summary['R5']['previous_month'] += 1

    return {
        "status": "success",
        "report_period": report_period_message,
        "report_period_month_year": report_period_month_year,
        "keyword_rankings": keyword_rankings,
        "seranking_raw_data": seranking_raw_data,
        "segment_summary": segment_summary,
        "ranking_change_distribution": ranking_change_distribution,
        "top_100_new_entries": top_100_new_entries,
        "top_100_disappeared": top_100_disappeared,
        "overall_rank_distribution": overall_rank_distribution,
        "message": "Successfully retrieved keyword ranking data from SERanking API."
    }


def get_clients_for_frontend():
    """
    Builds a simple clients list for frontend consumption using SERanking sites.
    Returns a dict with 'status' and 'clients' = [{id, name, domain?}].
    Note: GA4 properties are intentionally excluded (per requirement).
    """
    sites = get_seranking_sites_from_api()
    if sites is None:
        return {"status": "error", "message": "Failed to fetch sites from SERanking API."}

    clients_data = []
    for s in sites:
        # Extract minimal info for frontend
        client_entry = {
            "id": s.get("id"),
            "name": s.get("name") or "",
        }
        # Include domain if available in API result
        domain = s.get("domain") or s.get("url") or s.get("site_url")
        if domain:
            client_entry["domain"] = domain

        # Do NOT include any GA4 property fields (removed as per requirement)
        clients_data.append(client_entry)

    return {"status": "success", "clients": clients_data}
