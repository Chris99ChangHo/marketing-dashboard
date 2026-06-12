// domElements.js: Centralizes references to all DOM elements used in the application.
//
// This module provides a single function to retrieve and organize references
// to all significant HTML elements (buttons, inputs, display areas, canvases)
// that are interacted with or updated by the JavaScript logic. This approach
// enhances code readability, simplifies maintenance, and prevents issues
// related to missing or incorrectly referenced DOM elements.
//
// Key Aspects:
// - Consolidates all `document.getElementById()` calls into one place.
// - Returns a structured object (`dom`) for easy access to elements throughout the application.
// - Improves maintainability: if an element's ID changes in HTML, only this file needs updating.
//
// Dependencies:
// - None (relies on standard browser DOM API)
//
// Key Functions:
// - getDomElements(): Returns an object containing references to all relevant DOM elements.

export function getDomElements() {
  // Ensure the DOM is fully loaded before accessing elements
  const dom = {
    // General UI Elements
    clientSelect: document.getElementById("clientSelect"),
    loadDataBtn: document.getElementById("loadDataBtn"),
    startDateInput: document.getElementById("startDate"),
    endDateInput: document.getElementById("endDate"),
    errorMessageDiv: document.getElementById("errorMessage"),

    // GA4 Audience data elements
    totalSessionsSpan: document.getElementById("totalSessions"),
    totalUsersSpan: document.getElementById("totalUsers"),
    avgEngagementTimeSpan: document.getElementById("avgEngagementTime"),
    newUsersSpan: document.getElementById("newUsers"),
    returningUsersSpan: document.getElementById("returningUsers"),
    totalPageViewsSpan: document.getElementById("totalPageViews"),
    pagePerVisitSpan: document.getElementById("pagePerVisit"),
    engagementRateSpan: document.getElementById("engagementRate"),
    lastMonthTotalPageViewsSpan: document.getElementById("lastMonthTotalPageViews"),
    lastMonthPagePerVisitSpan: document.getElementById("lastMonthPagePerVisit"),

    // Device/Traffic Audience data elements
    mobileUsersSpan: document.getElementById("mobileUsers"),
    desktopUsersSpan: document.getElementById("desktopUsers"),
    tabletUsersSpan: document.getElementById("tabletUsers"),
    lastMonthMobileUsersSpan: document.getElementById("lastMonthMobileUsers"),
    lastMonthDesktopUsersSpan: document.getElementById("lastMonthDesktopUsers"),
    lastMonthTabletUsersSpan: document.getElementById("lastMonthTabletUsers"),
    searchTrafficSpan: document.getElementById("searchTraffic"),
    referralTrafficSpan: document.getElementById("referralTraffic"),
    directTrafficSpan: document.getElementById("directTraffic"),
    socialTrafficSpan: document.getElementById("socialTraffic"),

    // Chart Canvas (Chart.js)
    deviceChartCanvas: document.getElementById("deviceChart"),
    trafficSourceChartCanvas: document.getElementById("trafficSourceChart"),
    rankingChangeDistributionChartCanvas: document.getElementById("rankingChangeDistributionChartCanvas"),

    // SERanking data elements
    serankingDataDiv: document.getElementById("serankingData"),
    serankingKeywordTable: document.getElementById("serankingKeywordTable"),
    top100NewEntriesList: document.getElementById("top100NewEntriesList"),
    top100DisappearedList: document.getElementById("top100DisappearedList"),
    combinedKeywordsTableContainer: document.getElementById("combinedKeywordsTableContainer"),

    // Google Ads input forms
    adsLocationInput: document.getElementById("adsLocation"),
    adsLanguageInput: document.getElementById("adsLanguage"),
    adsDevicesInput: document.getElementById("adsDevices"),
    adsDailyBudgetInput: document.getElementById("adsDailyBudget"),
    manualCampaignInput: document.getElementById("manualCampaign"),
    manualImpressionInput: document.getElementById("manualImpression"),
    manualCostInput: document.getElementById("manualCost"),
    manualInteractionsInput: document.getElementById("manualInteractions"),
    manualAvgCostInput: document.getElementById("manualAvgCost"),

    // Report Generation Buttons
    generateDashboardPdfBtn: document.getElementById("generateDashboardPdfBtn"),
    generatePdfReportBtn: document.getElementById("generatePdfReportBtn"),

    // AI Summary Section
    generateAiSummaryBtn: document.getElementById("generateAiSummaryBtn"),
    aiSummarySpinner: document.getElementById("aiSummarySpinner"),
    aiSummaryResult: document.getElementById("aiSummaryResult"),

    // Cover Image Modal Elements
    openFrontCoverModalBtn: document.getElementById("openFrontCoverModalBtn"),
    openBackCoverModalBtn: document.getElementById("openBackCoverModalBtn"),
    closeCoverImageModalBtn: document.getElementById("closeCoverImageModalBtn"),
    cancelCoverImageSelectionBtn: document.getElementById("cancelCoverImageSelectionBtn"),
    confirmCoverImageSelectionBtn: document.getElementById("confirmCoverImageSelectionBtn"),
    coverImageModal: document.getElementById("coverImageModal"),
    coverImageList: document.getElementById("coverImageList"),
    selectedFrontCoverPreview: document.getElementById("selectedFrontCoverPreview"),
    selectedBackCoverPreview: document.getElementById("selectedBackCoverPreview"),
  };
  return dom;
}