# ga4_service.py: Handles logic related to Google Analytics 4 data.
#
# This module is responsible for interacting with the Google Analytics Data API (GA4)
# to fetch various web analytics metrics. It processes the raw API responses
# into a structured format suitable for display on the dashboard and PDF reports.
# It also calculates comparative data for different time periods.
#
# Dependencies:
# - google.analytics.data_v1beta (Google Analytics Data API client library)
# - Standard library modules: datetime, logging
# - Internal modules: auth_service (for Google API credentials)
#
# Key Functions:
# - get_ga4_data_internal(requested_ga4_property_id, start_date_str, end_date_str):
#   Fetches GA4 data for a specified property and date range, including current
#   and previous period comparisons, device usage, and traffic sources. Returns
#   a comprehensive dictionary of processed GA4 metrics.

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)
from datetime import date, timedelta, datetime
import logging
from auth_service import get_global_credentials

logger = logging.getLogger(__name__)

def get_ga4_data_internal(requested_ga4_property_id, start_date_str, end_date_str):
    logger.debug(f"DEBUG: _get_ga4_data_internal called. start_date_str='{start_date_str}', end_date_str='{end_date_str}'")

    credentials = get_global_credentials()
    if not credentials or not credentials.valid:
        logger.error("GA4 API: Google Analytics authentication information is invalid.")
        raise Exception("Google Analytics authentication is required. Please restart the server or check client_secret.json.")

    if not requested_ga4_property_id:
        logger.error("GA4 API: property_id was not provided.")
        raise ValueError("GA4 Property ID is required.")
    
    try:
        current_end_date_obj = date.today() if end_date_str == 'today' else datetime.strptime(end_date_str, '%Y-%m-%d').date()
        if start_date_str == '7daysAgo':
            current_start_date_obj = current_end_date_obj - timedelta(days=6)
        else:
            current_start_date_obj = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        
        period_length_days = (current_end_date_obj - current_start_date_obj).days + 1
        last_month_start_date_obj = current_start_date_obj - timedelta(days=period_length_days)
        last_month_end_date_obj = current_end_date_obj - timedelta(days=period_length_days)

        logger.debug(f"GA4 Period - Current: {current_start_date_obj} ~ {current_end_date_obj}")
        logger.debug(f"GA4 Period - Last Month: {last_month_start_date_obj} ~ {last_month_end_date_obj}")
        
    except ValueError as e:
        logger.error(f"GA4 API: Date format error: {e}")
        raise ValueError("Invalid date format. Please use YYYY-MM-DD.")

    request_body_current = RunReportRequest(
        property=f"properties/{requested_ga4_property_id}",
        metrics=[
            Metric(name="activeUsers"),
            Metric(name="newUsers"),
            Metric(name="sessions"),
            Metric(name="screenPageViews"),
            Metric(name="engagementRate"),
            Metric(name="averageSessionDuration"),
            Metric(name="conversions")
        ],
        dimensions=[
            Dimension(name="date"),
            Dimension(name="deviceCategory"),
            Dimension(name="sessionSource"),
            Dimension(name="newVsReturning")
        ],
        date_ranges=[DateRange(start_date=current_start_date_obj.strftime('%Y-%m-%d'), end_date=current_end_date_obj.strftime('%Y-%m-%d'))],
    )

    request_body_last_month = RunReportRequest(
        property=f"properties/{requested_ga4_property_id}",
        metrics=[
            Metric(name="activeUsers"),
            Metric(name="sessions"),
            Metric(name="screenPageViews"),
        ],
        dimensions=[
            Dimension(name="deviceCategory"),
        ],
        date_ranges=[DateRange(start_date=last_month_start_date_obj.strftime('%Y-%m-%d'), end_date=last_month_end_date_obj.strftime('%Y-%m-%d'))],
    )

    client = BetaAnalyticsDataClient(credentials=credentials)
    response_current = client.run_report(request_body_current)
    response_last_month = client.run_report(request_body_last_month)

    report_data_current = []
    total_sessions_current = 0
    total_users_current = 0
    new_users_current = 0
    returning_users_current = 0
    total_page_views_current = 0
    average_session_duration_sum_current = 0
    engagement_rate_sum_for_avg_current = 0
    total_sessions_for_engagement_rate = 0

    device_users_current = {"desktop": 0, "mobile": 0, "tablet": 0}
    traffic_by_type_current = {"search": 0, "referral": 0, "direct": 0, "social": 0, "other": 0}

    for row in response_current.rows:
        row_data = {}
        for i, dimension_value in enumerate(row.dimension_values):
            row_data[response_current.dimension_headers[i].name] = dimension_value.value
        for i, metric_value in enumerate(row.metric_values):
            row_data[response_current.metric_headers[i].name] = metric_value.value
        report_data_current.append(row_data)

        sessions = int(float(row_data.get('sessions', 0)))
        active_users = int(float(row_data.get('activeUsers', 0)))
        screen_page_views = int(float(row_data.get('screenPageViews', 0)))
        engagement_rate = float(row_data.get('engagementRate', 0))
        average_session_duration = float(row_data.get('averageSessionDuration', 0))

        total_sessions_current += sessions
        total_users_current += active_users
        total_page_views_current += screen_page_views
        average_session_duration_sum_current += average_session_duration * sessions

        if sessions > 0:
            engagement_rate_sum_for_avg_current += engagement_rate * sessions
            total_sessions_for_engagement_rate += sessions

        user_type_dimension = row_data.get('newVsReturning')
        if user_type_dimension == 'new':
            new_users_current += active_users 
        elif user_type_dimension == 'returning':
            returning_users_current += active_users
        
        device = row_data.get('deviceCategory', '').lower()
        if device in device_users_current:
            device_users_current[device] += active_users

        source = row_data.get('sessionSource', 'unknown').lower()
        if any(s in source for s in ['google', 'bing', 'naver', 'daum', 'duckduckgo', 'yandex']) or 'organic' in source or 'cpc' in source or 'paid search' in source:
            traffic_by_type_current['search'] += sessions
        elif 'direct' in source or '(direct)' in source:
            traffic_by_type_current['direct'] += sessions
        elif any(s in source for s in ['facebook', 'instagram', 'twitter', 'linkedin', 'pinterest', 'reddit', 'youtube', 'social']):
            traffic_by_type_current['social'] += sessions
        elif 'referral' in source or 'blog' in source or 'forum' in source or 'link' in source:
            traffic_by_type_current['referral'] += sessions
        else: 
            traffic_by_type_current['other'] += sessions


    total_page_views_last_month = 0
    device_users_last_month = {"desktop": 0, "mobile": 0, "tablet": 0}
    total_sessions_last_month = 0

    for row in response_last_month.rows:
        row_data = {}
        for i, dimension_value in enumerate(row.dimension_values):
            row_data[response_last_month.dimension_headers[i].name] = dimension_value.value
        for i, metric_value in enumerate(row.metric_values):
            row_data[response_last_month.metric_headers[i].name] = metric_value.value
        
        sessions = int(float(row_data.get('sessions', 0)))
        screen_page_views = int(float(row_data.get('screenPageViews', 0)))
        active_users = int(float(row_data.get('activeUsers', 0)))

        total_page_views_last_month += screen_page_views
        total_sessions_last_month += sessions

        device = row_data.get('deviceCategory', '').lower()
        if device in device_users_last_month:
            device_users_last_month[device] += active_users

    page_per_visit_current = total_page_views_current / total_sessions_current if total_sessions_current > 0 else 0
    avg_engagement_time_current = average_session_duration_sum_current / total_sessions_current if total_sessions_current > 0 else 0
    engagement_rate_current = (engagement_rate_sum_for_avg_current / total_sessions_for_engagement_rate) if total_sessions_for_engagement_rate > 0 else 0

    page_per_visit_last_month = total_page_views_last_month / total_sessions_last_month if total_sessions_last_month > 0 else 0

    user_acquisition_sources = []
    for source, amount in traffic_by_type_current.items():
        # Map internal keys to more readable names for the report
        display_name = source.replace('_', ' ').title() + ' Traffic' if source != 'other' else 'Other Traffic'
        user_acquisition_sources.append({"source": display_name, "users": amount})

    # Sort by users in descending order and take top 5
    user_acquisition_sources = sorted(user_acquisition_sources, key=lambda x: x['users'], reverse=True)[:5]

    return {
        "status": "success",
        "total_sessions": total_sessions_current,
        "total_users": total_users_current,
        "new_users": new_users_current,
        "returning_users": returning_users_current,
        "total_page_views": total_page_views_current,
        "page_per_visit": round(page_per_visit_current, 2),
        "average_engagement_time": round(avg_engagement_time_current, 2),
        "engagement_rate": round(engagement_rate_current, 4),
        "device_users": device_users_current,
        "traffic_sources": traffic_by_type_current,
        "traffic_by_type": traffic_by_type_current, # Same data as traffic_sources, can be consolidated
        "last_month_total_page_views": total_page_views_last_month,
        "last_month_page_per_visit": round(page_per_visit_last_month, 2),
        "last_month_device_users": device_users_last_month,
        "raw_data": report_data_current,
        "user_acquisition_sources": user_acquisition_sources,
        "message": "Successfully fetched GA4 data.",
        "previous_period_data": { # Add previous period data
            "total_page_views": total_page_views_last_month,
            "page_per_visit": page_per_visit_last_month,
            "device_users": device_users_last_month,
            "total_sessions": total_sessions_last_month,
        }
    }