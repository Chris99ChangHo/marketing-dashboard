// ga4DisplayService.js: Handles displaying Google Analytics 4 data on the UI.
//
// This module is responsible for updating the DOM elements with Google Analytics 4 (GA4) data.
// It takes the fetched GA4 data and populates the relevant HTML elements on the dashboard,
// ensuring that the data is formatted correctly for display.
//
// Key Aspects:
// - Centralizes the logic for rendering GA4 metrics (sessions, users, page views, etc.)
//   and device/traffic source breakdowns.
// - Provides functions to clear the display or set a loading state, ensuring a responsive UI.
// - Utilizes `toLocaleString()` for proper number formatting.
//
// Dependencies:
// - domElements.js (for accessing DOM element references)
//
// Key Functions:
// - updateGa4Display(dom, ga4Data): Populates the dashboard with GA4 data.
// - clearGa4Display(dom, value): Clears all GA4 related display elements.
// - setGa4LoadingState(dom): Sets a loading message for GA4 display elements.

export function updateGa4Display(dom, ga4Data) {
    dom.totalSessionsSpan.textContent = ga4Data.total_sessions?.toLocaleString() || 'N/A';
    dom.totalUsersSpan.textContent = ga4Data.total_users?.toLocaleString() || 'N/A';
    dom.avgEngagementTimeSpan.textContent = ga4Data.average_engagement_time ? `${ga4Data.average_engagement_time.toFixed(1)}s` : '0s';
    dom.newUsersSpan.textContent = ga4Data.new_users?.toLocaleString() || '0';
    dom.returningUsersSpan.textContent = ga4Data.returning_users?.toLocaleString() || '0';
    dom.totalPageViewsSpan.textContent = ga4Data.total_page_views?.toLocaleString() || '0';
    dom.pagePerVisitSpan.textContent = ga4Data.page_per_visit ? ga4Data.page_per_visit.toFixed(2) : '0';
    dom.engagementRateSpan.textContent = ga4Data.engagement_rate ? `${(ga4Data.engagement_rate * 100).toFixed(1)}%` : '0%';
    dom.lastMonthTotalPageViewsSpan.textContent = ga4Data.last_month_total_page_views?.toLocaleString() || '0';
    dom.lastMonthPagePerVisitSpan.textContent = ga4Data.last_month_page_per_visit ? ga4Data.last_month_page_per_visit.toFixed(2) : '0';
    dom.mobileUsersSpan.textContent = ga4Data.device_users.mobile?.toLocaleString() || '0';
    dom.desktopUsersSpan.textContent = ga4Data.device_users.desktop?.toLocaleString() || '0';
    dom.tabletUsersSpan.textContent = ga4Data.device_users.tablet?.toLocaleString() || '0';
    dom.lastMonthMobileUsersSpan.textContent = ga4Data.last_month_device_users.mobile?.toLocaleString() || '0';
    dom.lastMonthDesktopUsersSpan.textContent = ga4Data.last_month_device_users.desktop?.toLocaleString() || '0';
    dom.lastMonthTabletUsersSpan.textContent = ga4Data.last_month_device_users.tablet?.toLocaleString() || '0';
    dom.searchTrafficSpan.textContent = ga4Data.traffic_by_type.search?.toLocaleString() || '0';
    dom.referralTrafficSpan.textContent = ga4Data.traffic_by_type.referral?.toLocaleString() || '0';
    dom.directTrafficSpan.textContent = ga4Data.traffic_by_type.direct?.toLocaleString() || '0';
    dom.socialTrafficSpan.textContent = ga4Data.traffic_by_type.social?.toLocaleString() || '0';
}

export function clearGa4Display(dom, value = '') {
    const spans = [
        dom.totalSessionsSpan, dom.totalUsersSpan, dom.avgEngagementTimeSpan, dom.newUsersSpan, dom.returningUsersSpan,
        dom.totalPageViewsSpan, dom.pagePerVisitSpan, dom.engagementRateSpan, dom.lastMonthTotalPageViewsSpan,
        dom.lastMonthPagePerVisitSpan, dom.mobileUsersSpan, dom.desktopUsersSpan, dom.tabletUsersSpan,
        dom.lastMonthMobileUsersSpan, dom.lastMonthDesktopUsersSpan, dom.lastMonthTabletUsersSpan,
        dom.searchTrafficSpan, dom.referralTrafficSpan, dom.directTrafficSpan, dom.socialTrafficSpan
    ];
    spans.forEach(span => { if (span) span.textContent = value; });
}

export function setGa4LoadingState(dom) {
    const loadingText = 'Loading...';
    const spansToUpdate = [
        dom.totalSessionsSpan, dom.totalUsersSpan, dom.avgEngagementTimeSpan,
        dom.newUsersSpan, dom.returningUsersSpan, dom.totalPageViewsSpan,
        dom.pagePerVisitSpan, dom.engagementRateSpan, dom.lastMonthTotalPageViewsSpan,
        dom.lastMonthPagePerVisitSpan, dom.mobileUsersSpan, dom.desktopUsersSpan,
        dom.tabletUsersSpan, dom.lastMonthMobileUsersSpan, dom.lastMonthDesktopUsersSpan,
        dom.lastMonthTabletUsersSpan, dom.searchTrafficSpan, dom.referralTrafficSpan,
        dom.directTrafficSpan, dom.socialTrafficSpan
    ];

    spansToUpdate.forEach(span => {
        if (span) {
            span.textContent = loadingText;
        }
    });
}
