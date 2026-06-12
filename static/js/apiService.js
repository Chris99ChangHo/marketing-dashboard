// apiService.js: Handles all API communication with the backend.
//
// This module centralizes all asynchronous requests made from the frontend
// to the Flask backend API. It provides functions to fetch data related to
// clients, Google Analytics 4, SE Ranking, AI summaries, and PDF cover images,
// as well as initiating PDF report generation.
//
// Key Aspects:
// - Encapsulates fetch API calls, ensuring consistent error handling and
//   credential management (e.g., sending JWT cookies).
// - Provides clear, asynchronous functions for each API endpoint interaction.
// - Throws detailed errors for failed API requests, aiding in debugging.
//
// Dependencies:
// - Standard browser Fetch API
//
// Key Functions:
// - fetchClients(): Retrieves the list of available clients/sites.
// - fetchGa4Data(): Fetches Google Analytics 4 data for a specified property and date range.
// - fetchSerankingData(): Fetches SE Ranking data for a specified site and date range.
// - fetchAiSummary(): Requests an AI-generated summary based on GA4 and SERanking data.
// - fetchCoverImages(): Fetches URLs for dynamic PDF cover images from WordPress.
// - generatePdfReport(): Initiates the PDF report generation process on the backend.

export async function fetchClients() {
    const response = await fetch(`/api/sites`, {
        credentials: 'same-origin'   // JWT cookies are sent automatically
    });
    if (!response.ok) {
        throw new Error(`Backend connection or client list load error: ${response.statusText}`);
    }
    return await response.json();
}

export async function fetchGa4Data(propertyId, startDate, endDate) {
    const apiUrl = `/api/ga4_data?property_id=${propertyId}&start_date=${startDate}&end_date=${endDate}`;
    const response = await fetch(apiUrl, {
        credentials: 'same-origin'
    });
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`GA4 data fetch failed: ${response.status} - ${response.statusText}. Response: ${errorText.substring(0, 100)}...`);
    }
    return await response.json();
}

export async function fetchSerankingData(siteId, startDate, endDate) {
    const apiUrl = `/api/seranking_data?site_id=${siteId}&start_date=${startDate}&end_date=${endDate}`;
    const response = await fetch(apiUrl, {
        credentials: 'same-origin'
    });
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`SERanking data fetch failed: ${response.status} - ${response.statusText}. Response: ${errorText.substring(0, 100)}...`);
    }
    return await response.json();
}

export async function fetchAiSummary(ga4Data, serankingData, clientName) {
    const response = await fetch(`/api/ai_summary`, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            ga4_data: ga4Data, 
            seranking_data: serankingData, 
            client_name: clientName 
        }),
    });
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`AI Summary fetch failed: ${response.status} - ${errorText}`);
    }
    return await response.json();
}

export async function fetchCoverImages(category = 'front') {
    const response = await fetch(`/api/cover-images?category=${category}`, {
        credentials: 'same-origin'
    });

    if (!response.ok) {
        const errorText = await response.text();
        console.error(`[API Service] Failed to fetch cover images (${response.status}):`, errorText);
        throw new Error(`Failed to fetch cover images: ${response.status} - ${errorText.substring(0, 100)}...`);
    }

    const contentType = response.headers.get("content-type");
    if (!contentType || !contentType.includes("application/json")) {
        const errorText = await response.text();
        console.error(`[API Service] Expected JSON, but received: ${contentType}. Response:`, errorText);
        throw new Error(`Invalid response type for cover images. Expected JSON. Received: ${contentType}. Content: ${errorText.substring(0, 100)}...`);
    }

    try {
        return await response.json();
    } catch (e) {
        const errorText = await response.text();
        console.error(`[API Service] JSON parsing failed for cover images:`, e, `Raw response:`, errorText);
        throw new Error(`JSON parsing failed for cover images: ${e.message}. Raw: ${errorText.substring(0, 100)}...`);
    }
}

export async function generatePdfReport(reportData) {
    const response = await fetch(`/generate-pdf-report`, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(reportData),
    });
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`PDF report generation failed: ${response.status} - ${errorText}`);
    }
    return response.blob();
}