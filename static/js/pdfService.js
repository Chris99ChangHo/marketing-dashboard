// pdfService.js: Handles the logic for PDF generation requests.
//
// This module provides the client-side functionality for generating, downloading,
// and previewing PDF reports. It communicates with the backend API to initiate
// PDF creation and handles the resulting PDF data (Blob).
//
// Key Aspects:
// - Centralized functions for making PDF generation requests to the backend.
// - Provides utilities for downloading the generated PDF files.
// - Offers a preview function to open PDFs in a new browser tab.
// - Handles error propagation from backend PDF generation failures.
//
// Dependencies:
// - Standard browser Fetch API
//
// Key Functions:
// - fetchPdfFromBackend(endpoint, data): A generic helper to send PDF generation requests.
// - generateStandardReport(reportData): Initiates the generation of the main marketing report PDF.
// - generateDashboardPdf(dashboardHtml): Initiates the generation of a PDF from the current dashboard view.
// - downloadPdf(blob, fileName): Downloads a given PDF Blob to the user's device.
// - previewPdfInNewTab(blob): Opens a given PDF Blob in a new browser tab for viewing.

/**
 * Sends a request to the backend to generate a PDF and returns the PDF blob.
 * @param {string} endpoint - Backend API endpoint (e.g., '/generate-standard-report').
 * @param {object} data - Payload to send in the request body.
 * @returns {Promise<Blob>} PDF data as a Blob.
 */
async function fetchPdfFromBackend(endpoint, data) {
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`PDF generation failed at ${endpoint}: ${response.status} ${response.statusText} - ${errorText}`);
        }
        return await response.blob();
    } catch (error) {
        // Rethrow so the UI layer can handle the error in detail.
        throw error;
    }
}

/**
 * Generates a standard report PDF.
 * @param {object} reportData - Data required to generate the report.
 * @returns {Promise<Blob>} PDF data as a Blob.
 */
export function generateStandardReport(reportData) {
    return fetchPdfFromBackend('/generate-pdf-report', reportData);
}

/**
 * Generates a PDF from the current dashboard HTML.
 * @param {string} dashboardHtml - The innerHTML of the dashboard to convert to PDF.
 * @returns {Promise<Blob>} PDF data as a Blob.
 */
export function generateDashboardPdf(dashboardHtml) {
    // Requires a matching backend endpoint like /generate-dashboard-pdf.
    return fetchPdfFromBackend('/generate-dashboard-pdf', { html_content: dashboardHtml });
}

// --- PDF utilities ---

/**
 * Triggers a download for the given PDF blob.
 * @param {Blob} blob - PDF data to download.
 * @param {string} fileName - Suggested file name (e.g., 'report.pdf').
 */
export function downloadPdf(blob, fileName) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = fileName;

    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

/**
 * Opens the given PDF blob in a new browser tab for preview.
 * @param {Blob} blob - PDF data to preview.
 */
export function previewPdfInNewTab(blob) {
    const url = window.URL.createObjectURL(blob);
    window.open(url, '_blank');
    // Give a slight delay so the browser can move focus to the new tab before revoking the URL.
    setTimeout(() => window.URL.revokeObjectURL(url), 100);
}
