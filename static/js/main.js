// main.js: The main entry point for the frontend application logic.
//
// This script orchestrates the entire client-side behavior of the marketing dashboard.
// It initializes the UI, fetches data from the backend APIs (GA4, SERanking, AI Summary),
// renders charts and tables, handles user interactions, and manages PDF report generation.
//
// Key Aspects:
// - Initializes DOM elements and sets up event listeners for user interactions.
// - Manages application state, including client data, GA4 data, and SERanking data.
// - Coordinates data loading and display updates across various UI components.
// - Triggers PDF generation for both dashboard snapshots and comprehensive reports.
// - Integrates with JWT for secure session management and token refreshing.
//
// Dependencies:
// - Local JavaScript modules: domElements.js, utils.js, apiService.js, chartService.js,
//   ga4DisplayService.js, serankingDisplayService.js, pdfService.js, uiService.js,
//   jwt-manager.js, session-guard.js
// - External libraries: Chart.js, html2canvas, jspdf
//
// Key Functions:
// - loadDataForClient(): Fetches and displays GA4 and SERanking data for the selected client.
// - handleGenerateDashboardPdf(): Generates a PDF of the current dashboard view.
// - handleGenerateStandardReport(): Generates a comprehensive PDF marketing report.
// - handleGenerateAiSummary(): Requests and displays an AI-powered summary of the data.
// - initializeApp(): Sets up initial client data, date ranges, and loads initial data.
// - destroyAllCharts(): Clears all Chart.js instances to prevent memory leaks.

import { getDomElements } from './domElements.js';
import { formatDate } from './utils.js';
import { fetchClients, fetchGa4Data, fetchSerankingData, fetchAiSummary, fetchCoverImages } from './apiService.js';
import { createDeviceChart, createRankingChangeDistributionChart, createTrafficSourceChart, destroyChart } from './chartService.js';
import { updateGa4Display, clearGa4Display } from './ga4DisplayService.js';
import { renderSerankingData, updateKeywordRankingTables, updateTop100Lists } from './serankingDisplayService.js';
import { generateStandardReport, downloadPdf, previewPdfInNewTab } from './pdfService.js';
import { clearAllDisplays, setLoadingState, showErrorMessage, showSuccessMessage, initializeCoverImageModal, getSelectedCoverImageUrls } from './uiService.js';
import { initializeJwtManager } from './jwt-manager.js';

document.addEventListener('DOMContentLoaded', () => {
    // --- State Management ---
    const dom = getDomElements();
    let clients = [];
    let latestGa4Data = null;
    let latestSerankingData = null;
    let selectedCoverImageUrl = null;
    let deviceChart = null;
    let trafficSourceChart = null;
    let rankingChangeDistributionChart = null;

    // --- Chart Management ---
    function destroyAllCharts() {
        deviceChart = destroyChart(deviceChart);
        trafficSourceChart = destroyChart(trafficSourceChart);
        rankingChangeDistributionChart = destroyChart(rankingChangeDistributionChart);
    }

    // --- Data Loading and Display ---
    async function loadDataForClient() {
        showErrorMessage(dom, '');
        const selectedClientIndex = dom.clientSelect.value;
        const selectedClient = clients[selectedClientIndex];

        if (!selectedClient) {
            showErrorMessage(dom, 'Please select a client to view data.');
            clearAllDisplays(dom);
            destroyAllCharts();
            return;
        }

        setLoadingState(dom);
        destroyAllCharts();

        const startDate = dom.startDateInput.value;
        const endDate = dom.endDateInput.value;

        try {
            const ga4Data = await fetchGa4Data(selectedClient.ga4PropertyId, startDate, endDate);
            if (ga4Data.status === 'success') {
                latestGa4Data = ga4Data;
                updateGa4Display(dom, ga4Data);
                if (dom.deviceChartCanvas) {
                    deviceChart = createDeviceChart(dom.deviceChartCanvas.getContext('2d'), ga4Data.device_users);
                }
                if (dom.trafficSourceChartCanvas) {
                    trafficSourceChart = createTrafficSourceChart(dom.trafficSourceChartCanvas.getContext('2d'), ga4Data.traffic_sources);
                }
            } else {
                latestGa4Data = null;
                showErrorMessage(dom, `GA4 Data Error: ${ga4Data.message || 'Unknown'}`);
                clearGa4Display(dom);
            }

            const serankingData = await fetchSerankingData(selectedClient.serankingSiteId, startDate, endDate);
            if (serankingData.status === 'success') {
                latestSerankingData = serankingData; 
                renderSerankingData(dom, serankingData);
                updateTop100Lists(dom, serankingData.top_100_new_entries, serankingData.top_100_disappeared);
                if (dom.rankingChangeDistributionChartCanvas && serankingData.ranking_change_distribution) {
                    rankingChangeDistributionChart = createRankingChangeDistributionChart(dom.rankingChangeDistributionChartCanvas.getContext('2d'), serankingData.ranking_change_distribution);
                }
                updateKeywordRankingTables(dom, serankingData.keyword_rankings);
            } else {
                latestSerankingData = null;
                showErrorMessage(dom, `SERanking Data Error: ${serankingData.message || 'Unknown'}`);
            }

        } catch (error) {
            latestGa4Data = null;
            latestSerankingData = null;
            showErrorMessage(dom, `A fatal error occurred: ${error.message}`);
            clearAllDisplays(dom);
            destroyAllCharts();
        } finally {
            window.scrollTo({ top: 0, behavior: 'smooth' }); // Scroll to top after loading data
        }
    }

    // --- PDF Generation Handler ---
    async function handleGenerateDashboardPdf() {
        window.scrollTo({ top: 0, behavior: 'smooth' });
        showSuccessMessage(dom, 'Generating Dashboard PDF preview...');
        const { jsPDF } = window.jspdf;
        const dashboardContent = document.getElementById('mainDashboardContainer');
        const buttonsSection = dashboardContent.querySelector('.gap-6.mt-10');
        
        if (buttonsSection) buttonsSection.style.visibility = 'hidden';

        try {
            const canvas = await html2canvas(dashboardContent, {
                scale: 2,
                useCORS: true,
                logging: false,
                onclone: (document) => {
                    // Ensure all charts are resized correctly
                    document.querySelectorAll('canvas').forEach(canvas => {
                        const chartInstance = Chart.getChart(canvas);
                        if (chartInstance) {
                            chartInstance.resize();
                        }
                    });
                }
            });

            if (buttonsSection) buttonsSection.style.visibility = 'visible';

            const imgData = canvas.toDataURL('image/png');
            const pdf = new jsPDF({
                orientation: 'p',
                unit: 'px',
                format: [canvas.width, canvas.height]
            });

            pdf.addImage(imgData, 'PNG', 0, 0, canvas.width, canvas.height);
            const pdfBlob = pdf.output('blob');
            previewPdfInNewTab(pdfBlob);
            showSuccessMessage(dom, 'Dashboard PDF preview generated successfully!');

        } catch (error) {
            if (buttonsSection) buttonsSection.style.visibility = 'visible';
            showErrorMessage(dom, `Dashboard PDF generation failed: ${error.message}`);
            console.error(error);
        }
    }

    async function handleGenerateStandardReport() {
        window.scrollTo({ top: 0, behavior: 'smooth' });
        showErrorMessage(dom, '');
        const selectedClientIndex = dom.clientSelect.value;
        const selectedClient = clients[selectedClientIndex];

        if (!selectedClient || !latestGa4Data || !latestSerankingData) {
            showErrorMessage(dom, 'Please load data first before generating a report.');
            return;
        }

        const selectedCovers = getSelectedCoverImageUrls();

        const reportData = {
            client_id: selectedClient.id,
            clientName: selectedClient.name,
            clientWebsite: selectedClient.domain || 'N/A',
            reportDate: new Date().toLocaleDateString('en-AU'),
            startDate: dom.startDateInput.value,
            endDate: dom.endDateInput.value,
            ga4_data: latestGa4Data,
            seranking_data: latestSerankingData,
            google_ads_manual_data: {
                location: dom.adsLocationInput.value,
                language: dom.adsLanguageInput.value,
                devices: dom.adsDevicesInput.value,
                daily_budget: dom.adsDailyBudgetInput.value,
                campaign: dom.manualCampaignInput.value,
                impression: dom.manualImpressionInput.value,
                cost: dom.manualCostInput.value,
                interactions: dom.manualInteractionsInput.value,
                avg_cost: dom.manualAvgCostInput.value
            },
            front_cover_image_url: selectedCovers.front,
            back_cover_image_url: selectedCovers.back
        };

        try {
            showSuccessMessage(dom, 'Generating PDF report... please wait.');
            const blob = await generateStandardReport(reportData);
            const fileName = `${reportData.clientName.replace(/[^a-zA-Z0-9_]/g, '')}_${formatDate(new Date(reportData.endDate))}_Report.pdf`;
            downloadPdf(blob, fileName);
            showSuccessMessage(dom, 'PDF report generated successfully!');
        } catch (error) {
            showErrorMessage(dom, `PDF generation failed: ${error.message}`);
        }
    }

    // --- Application Initialization ---
    async function initializeApp() {
        showErrorMessage(dom, '');
        try {
            const [clientData, coverImageData] = await Promise.all([
                fetchClients(),
                fetchCoverImages()
            ]);

            clients = clientData.clients || [];
            if (clients.length > 0) {
                dom.clientSelect.innerHTML = '';
                clients.forEach((client, index) => {
                    const option = document.createElement('option');
                    option.value = index;
                    option.textContent = client.name;
                    dom.clientSelect.appendChild(option);
                });

                dom.clientSelect.value = 0;
                const today = new Date();
                const thirtyDaysAgo = new Date(new Date().setDate(today.getDate() - 30));
                dom.endDateInput.value = formatDate(today);
                dom.startDateInput.value = formatDate(thirtyDaysAgo);

                await loadDataForClient();
            } else {
                showErrorMessage(dom, 'No clients found.');
                dom.clientSelect.innerHTML = '<option value="">No Clients</option>';
                clearAllDisplays(dom);
            }

            } catch (error) {
            showErrorMessage(dom, `Initialization failed: ${error.message}`);
            dom.clientSelect.innerHTML = '<option value="">Failed to load</option>';
            clearAllDisplays(dom);
        }
    }

    // --- Event Listeners ---
    dom.loadDataBtn.addEventListener('click', loadDataForClient);
    dom.clientSelect.addEventListener('change', loadDataForClient);
    dom.generateDashboardPdfBtn.addEventListener('click', handleGenerateDashboardPdf);
    dom.generatePdfReportBtn.addEventListener('click', handleGenerateStandardReport);
    dom.generateAiSummaryBtn.addEventListener('click', handleGenerateAiSummary);

    // --- AI Summary Generation Handler ---
    async function handleGenerateAiSummary() {
        showErrorMessage(dom, '');
        const selectedClientIndex = dom.clientSelect.value;
        const selectedClient = clients[selectedClientIndex];

        if (!selectedClient || !latestGa4Data || !latestSerankingData) {
            showErrorMessage(dom, 'Please load data first before generating an AI summary.');
            return;
        }

        dom.aiSummarySpinner.classList.remove('hidden');
        dom.aiSummaryResult.textContent = 'Generating insights...';

        try {
            const result = await fetchAiSummary(latestGa4Data, latestSerankingData, selectedClient.name);
            dom.aiSummaryResult.textContent = result.summary;
        } catch (error) {
            const errorMessage = `AI Summary generation failed: ${error.message}`;
            showErrorMessage(dom, errorMessage);
            dom.aiSummaryResult.textContent = errorMessage;
        } finally {
            dom.aiSummarySpinner.classList.add('hidden');
        }
    }

    // --- Application Start ---
    initializeJwtManager(); // Initialize security system (interceptor) first
    initializeCoverImageModal(dom, { fetchCoverImages }); // Initialize modal

    // --- Application Start ---
    // Check APP_CONTEXT injected directly from the server and initialize the app immediately.
    if (window.APP_CONTEXT && window.APP_CONTEXT.userInfo) {
        console.log('[MAIN] App context found. Initializing app immediately.');
        initializeApp();

        // Only initialize SessionGuard if not in development environment
        if (window.APP_CONTEXT.userInfo.FLASK_ENV !== 'development') {
            window.sessionGuard = new SessionGuard();
        } else {
            console.log('[MAIN] Development mode detected. SessionGuard not initialized.');
        }

    } else {
        console.error('[MAIN] App context not found. App cannot start. This may indicate a server-side rendering issue or a problem with authentication.');
        showErrorMessage(dom, 'Fatal Error: Application context is missing. Please contact support.');
    }

    // --- Scroll to top immediately on page load ---
    window.scrollTo({ top: 0, behavior: 'auto' });
});