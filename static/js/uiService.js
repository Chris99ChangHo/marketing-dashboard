let selectedFrontCoverUrl = null;
let selectedBackCoverUrl = null;
let currentSelectionContext = null; // 'front' or 'back'

// --- Modal Control ---
export function initializeCoverImageModal(dom, apiService) {
    const modal = dom.coverImageModal;

    function openModal(context) {
        currentSelectionContext = context;
        modal.classList.remove('hidden');
        loadCoverImages(dom, apiService, context);
    }

    function closeModal() {
        modal.classList.add('hidden');
        currentSelectionContext = null;
    }

    dom.openFrontCoverModalBtn.addEventListener('click', () => openModal('front'));
    dom.openBackCoverModalBtn.addEventListener('click', () => openModal('back'));

    dom.closeCoverImageModalBtn.addEventListener('click', closeModal);
    dom.cancelCoverImageSelectionBtn.addEventListener('click', closeModal);

    dom.confirmCoverImageSelectionBtn.addEventListener('click', () => {
        if (currentSelectionContext === 'front' && dom.selectedFrontCoverPreview.dataset.tempUrl) {
            selectedFrontCoverUrl = dom.selectedFrontCoverPreview.dataset.tempUrl;
            dom.selectedFrontCoverPreview.src = selectedFrontCoverUrl;
        } else if (currentSelectionContext === 'back' && dom.selectedBackCoverPreview.dataset.tempUrl) {
            selectedBackCoverUrl = dom.selectedBackCoverPreview.dataset.tempUrl;
            dom.selectedBackCoverPreview.src = selectedBackCoverUrl;
        }
        closeModal();
    });
}

async function loadCoverImages(dom, apiService, category) {
    const imageListDiv = dom.coverImageList;
    imageListDiv.innerHTML = '<p class="col-span-full text-center text-gray-500">Loading images...</p>';

    try {
        const data = await apiService.fetchCoverImages(category);
        const imageUrls = data.image_urls;

        if (!imageUrls || imageUrls.length === 0) {
            imageListDiv.innerHTML = `<p class="col-span-full text-center text-red-500">No images found for ${category} covers.</p>`;
            return;
        }

        imageListDiv.innerHTML = ''; // Clear loading text

        imageUrls.forEach(url => {
            const imgContainer = document.createElement('div');
            imgContainer.className = 'relative cursor-pointer group border-4 border-transparent rounded-lg transition hover:border-blue-500';
            
            const img = document.createElement('img');
            img.src = url;
            img.alt = "Cover Image";
            img.className = 'w-full h-48 object-cover rounded-md';

            imgContainer.appendChild(img);
            imageListDiv.appendChild(imgContainer);

            imgContainer.addEventListener('click', () => {
                document.querySelectorAll('#coverImageList .border-blue-500').forEach(el => el.classList.remove('border-blue-500'));
                imgContainer.classList.add('border-blue-500');
                
                if (currentSelectionContext === 'front') {
                    dom.selectedFrontCoverPreview.dataset.tempUrl = url;
                } else if (currentSelectionContext === 'back') {
                    dom.selectedBackCoverPreview.dataset.tempUrl = url;
                }
            });
        });

    } catch (error) {
        console.error(`Error fetching ${category} cover images:`, error);
        imageListDiv.innerHTML = `<p class="col-span-full text-center text-red-500">Error: ${error.message}</p>`;
    }
}

export function getSelectedCoverImageUrls() {
    return { 
        front: selectedFrontCoverUrl,
        back: selectedBackCoverUrl
    };
}

// uiService.js: Manages general UI interactions and updates.
//
// This module provides functions for controlling various aspects of the user interface,
// including displaying messages (errors, success), managing loading states,
// and handling the selection of cover images for PDF reports.
// It centralizes UI-related logic to ensure consistency and reusability.
//
// Key Aspects:
// - Manages the state and display of the cover image selection modal.
// - Provides functions to clear all displayed data and set loading indicators.
// - Offers utility functions for showing error and success messages to the user.
//
// Dependencies:
// - domElements.js (for accessing DOM element references)
// - apiService.js (for fetching cover images)
//
// Key Functions:
// - initializeCoverImageModal(dom, apiService): Sets up the cover image selection modal and its event listeners.
// - getSelectedCoverImageUrls(): Returns the URLs of the currently selected front and back cover images.
// - clearAllDisplays(dom): Resets all data display elements on the dashboard.
// - setLoadingState(dom): Sets all display elements to a loading state.
// - showErrorMessage(dom, message): Displays an error message to the user.
// - showSuccessMessage(dom, message): Displays a success message to the user.

export function clearAllDisplays(dom) {
    const spans = [
        dom.totalSessionsSpan, dom.totalUsersSpan, dom.avgEngagementTimeSpan, dom.newUsersSpan, dom.returningUsersSpan,
        dom.totalPageViewsSpan, dom.pagePerVisitSpan, dom.engagementRateSpan, dom.lastMonthTotalPageViewsSpan,
        dom.lastMonthPagePerVisitSpan, dom.mobileUsersSpan, dom.desktopUsersSpan, dom.tabletUsersSpan,
        dom.lastMonthMobileUsersSpan, dom.lastMonthDesktopUsersSpan, dom.lastMonthTabletUsersSpan,
        dom.searchTrafficSpan, dom.referralTrafficSpan, dom.directTrafficSpan, dom.socialTrafficSpan
    ];
    spans.forEach(span => { if (span) span.textContent = ''; });

    if (dom.serankingDataDiv) dom.serankingDataDiv.innerHTML = '';
    if (dom.serankingKeywordTable) dom.serankingKeywordTable.innerHTML = '';
    if (dom.combinedKeywordsTableContainer) dom.combinedKeywordsTableContainer.innerHTML = '';
    if (dom.top100NewEntriesList) dom.top100NewEntriesList.innerHTML = '';
    if (dom.top100DisappearedList) dom.top100DisappearedList.innerHTML = '';

    const inputs = [
        dom.adsDailyBudgetInput, dom.adsLocationInput, dom.adsLanguageInput, dom.adsDevicesInput,
        dom.manualCampaignInput, dom.manualImpressionInput, dom.manualCostInput, dom.manualInteractionsInput, dom.manualAvgCostInput
    ];
    inputs.forEach(input => { if (input) input.value = ''; });
}

export function setLoadingState(dom) {
    const loadingText = 'Loading...';
    if (dom.errorMessageDiv) dom.errorMessageDiv.textContent = '';
    
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

    if (dom.serankingDataDiv) dom.serankingDataDiv.innerHTML = `<p class="mt-4 text-center text-blue-600">${loadingText}</p>`;
    if (dom.serankingKeywordTable) dom.serankingKeywordTable.innerHTML = '';
    if (dom.top100NewEntriesList) dom.top100NewEntriesList.innerHTML = `<li>${loadingText}</li>`;
    if (dom.top100DisappearedList) dom.top100DisappearedList.innerHTML = `<li>${loadingText}</li>`;
    if (dom.combinedKeywordsTableContainer) dom.combinedKeywordsTableContainer.innerHTML = `<p class="mt-4 text-center text-blue-600">${loadingText}</p>`;
}

export function showErrorMessage(dom, message) {
    if (dom.errorMessageDiv) {
        dom.errorMessageDiv.textContent = message;
        dom.errorMessageDiv.style.color = 'red';
    }
}

export function showSuccessMessage(dom, message) {
    if (dom.errorMessageDiv) {
        dom.errorMessageDiv.textContent = message;
        dom.errorMessageDiv.style.color = 'green';
    }
}
