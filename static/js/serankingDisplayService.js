// serankingDisplayService.js: Handles displaying SERanking data on the UI.
//
// This module is responsible for rendering and updating the SERanking data
// on the dashboard's user interface. It processes the raw keyword ranking
// data, calculates changes, and dynamically generates HTML tables and lists
// to present the information clearly.
//
// Key Aspects:
// - Populates the main keyword ranking table with current and previous ranks, and change indicators.
// - Renders separate lists for new entries in the Top 100 and keywords that disappeared from the Top 100.
// - Provides functions to update the UI based on fetched SERanking data.
// - Formats data for display, including handling missing values and calculating rank changes.
//
// Dependencies:
// - domElements.js (for accessing DOM element references)
//
// Key Functions:
// - renderSerankingData(dom, serankingData): Updates the main SERanking data display.
// - updateTop100Lists(dom, newEntries, disappearedEntries): Renders the lists of new and disappeared keywords.
// - updateKeywordRankingTables(dom, keywordRankings): Updates the combined keyword ranking change tables.

export function renderSerankingData(dom, serankingData) {
    if (dom.serankingDataDiv) {
        dom.serankingDataDiv.innerHTML = `<p class="text-xs text-gray-500">${serankingData.message || ''}</p>`;
    }

    if (dom.serankingKeywordTable && serankingData.keyword_rankings && serankingData.keyword_rankings.length > 0) {
        let tableHtml = `
            <table class="min-w-full bg-white rounded-lg shadow-md">
                <thead>
                    <tr>
                        <th class="py-2 px-4 bg-gray-100 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider rounded-tl-lg">Keyword</th>
                        <th class="py-2 px-4 bg-gray-100 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Current Rank</th>
                        <th class="py-2 px-4 bg-gray-100 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Previous Rank</th>
                        <th class="py-2 px-4 bg-gray-100 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider rounded-tr-lg">Change</th>
                    </tr>
                </thead>
                <tbody>
        `;
        serankingData.keyword_rankings.forEach(keyword => {
            const currentRank = parseInt(String(keyword.current_rank).split('/')[0]);
            const previousRank = parseInt(String(keyword.previous_rank).split('/')[0]);

            let changeText = '';
            let changeClass = '';

            if (!isNaN(previousRank) && !isNaN(currentRank) && previousRank > 0 && currentRank > 0) {
                const diff = previousRank - currentRank;
                if (diff > 0) {
                    changeText = `▲ ${diff}`;
                    changeClass = 'text-green-500 font-medium';
                } else if (diff < 0) {
                    changeText = `▼ ${Math.abs(diff)}`;
                    changeClass = 'text-gray-500 font-medium'; 
                } else {
                    changeText = '-';
                    changeClass = 'black font-medium'; // No change
                }
            } else if (currentRank > 0 && (isNaN(previousRank) || previousRank === 0 || previousRank > 100)) {
                changeText = '▲ New in Top 100';
                changeClass = 'text-blue-500 font-medium';
            } else if (previousRank > 0 && (isNaN(currentRank) || currentRank === 0 || currentRank > 100)) {
                changeText = '▼ Out of Top 100';
                changeClass = 'text-gray-500 font-medium';
            } else {
                changeText = ''; 
                changeClass = 'black font-medium';
            }

            tableHtml += `
                            <tr class="border-b border-gray-200 last:border-b-0">
                                <td class="py-2 px-4 text-sm text-gray-800">${keyword.keyword || 'N/A'}</td>
                                <td class="py-2 px-4 text-sm text-gray-800">${keyword.current_rank || 'N/A'}</td>
                                <td class="py-2 px-4 text-sm text-gray-800">${keyword.previous_rank || 'N/A'}</td>
                                <td class="py-2 px-4 text-sm ${changeClass}">${changeText}</td>
                            </tr>
                    `;
        });
        tableHtml += `
                </tbody>
            </table>
        `;
        serankingKeywordTable.innerHTML = tableHtml;
    } else if (dom.serankingKeywordTable) {
        dom.serankingKeywordTable.innerHTML = '<p class="mt-4 text-center text-gray-600">No keyword ranking data found.</p>';
    }
}

export function updateTop100Lists(dom, newEntries, disappearedEntries) {
    const renderTable = (container, headers, data, rowRenderer, noDataMessage) => {
        if (!container) return;
        container.innerHTML = '';

        const headerHtml = headers.map((header, index) => {
            let classes = "py-2 px-4 bg-gray-100 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider";
            if (index === 0) classes += " rounded-tl-lg";
            if (index === headers.length - 1) classes += " rounded-tr-lg";
            return `<th class="${classes}">${header}</th>`;
        }).join('');

        let tableHtml = `
            <div class="overflow-x-auto">
                <table class="min-w-full bg-white rounded-lg shadow-md mb-8">
                    <thead>
                        <tr>
                            ${headerHtml}
                        </tr>
                    </thead>
                    <tbody>
        `;

        if (!data || data.length === 0) {
            tableHtml += `
                <tr class="border-b border-gray-200 last:border-b-0">
                    <td colspan="${headers.length}" class="py-2 px-4 text-sm text-gray-800">${noDataMessage}</td>
                </tr>
            `;
        } else {
            tableHtml += data.map(rowRenderer).join('');
        }

        tableHtml += `
                    </tbody>
                </table>
            </div>
        `;
        container.innerHTML = tableHtml;
    };

    renderTable(
        dom.top100NewEntriesList,
        ['Keyword', 'Current Rank'],
        newEntries,
        (item) => `
            <tr class="border-b border-gray-200 last:border-b-0">
                <td class="py-2 px-4 text-sm text-gray-800">${item.keyword || 'N/A'}</td>
                <td class="py-2 px-4 text-sm text-gray-800">${item.rank === 0 ? 0 : item.rank || 'N/A'}</td>
            </tr>
        `,
        'No new entries in Top 100.'
    );

    renderTable(
        dom.top100DisappearedList,
        ['Keyword', 'Previous Rank'],
        disappearedEntries,
        (item) => `
            <tr class="border-b border-gray-200 last:border-b-0">
                <td class="py-2 px-4 text-sm text-gray-800">${item.keyword || 'N/A'}</td>
                <td class="py-2 px-4 text-sm text-gray-800">${item.rank === 0 ? 0 : item.rank || 'N/A'}</td>
            </tr>
        `,
        'No keywords disappeared from Top 100.'
    );
}

export function updateKeywordRankingTables(dom, keywordRankings) {
    if (!dom.combinedKeywordsTableContainer) {
        console.error("combinedKeywordsTableContainer element not found.");
        return;
    }
    dom.combinedKeywordsTableContainer.innerHTML = '';

    if (!keywordRankings || keywordRankings.length === 0) {
        dom.combinedKeywordsTableContainer.innerHTML = '<p class="mt-4 text-center text-gray-600">No keyword ranking changes to display.</p>';
        return;
    }

    const upKeywords = [];
    const downKeywords = [];
    const newKeywords = [];
    const disappearedKeywords = [];

    keywordRankings.forEach(keyword => {
        const currentRankStr = String(keyword.current_rank);
        const previousRankStr = String(keyword.previous_rank);

        const currentRank = parseInt(currentRankStr.split('/')[0]);
        const previousRank = parseInt(previousRankStr.split('/')[0]);

        if ((previousRankStr === 'NA/-' || isNaN(previousRank) || previousRank === 0 || previousRank > 100) && !isNaN(currentRank) && currentRank > 0 && currentRank <= 100) {
            newKeywords.push(keyword);
        } else if (!isNaN(currentRank) && currentRank > 0 && currentRank <= 100 && !isNaN(previousRank) && previousRank > 0 && previousRank <= 100) {
            if (currentRank < previousRank) {
                upKeywords.push(keyword);
            } else if (currentRank > previousRank) {
                downKeywords.push(keyword);
            }
        } else if (!isNaN(previousRank) && previousRank > 0 && previousRank <= 100 && (isNaN(currentRank) || currentRank === 0 || currentRank > 100)) {
            disappearedKeywords.push(keyword);
        }
    });

    let tableHtml = '';

    const renderSection = (title, keywords, changeDisplayFunc) => {
        if (keywords.length === 0) {
            return `<p class="text-center text-gray-600 mb-4">No ${title.toLowerCase()}.</p>`;
        }

        let sectionHtml = `
            <div class="overflow-x-auto">
                <table class="min-w-full bg-white rounded-lg shadow-md mb-8 w-full">
                    <thead>
                        <tr>
                            <th class="py-2 px-4 bg-gray-100 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider rounded-tl-lg">Keyword</th>
                            <th class="py-2 px-4 bg-gray-100 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Current Rank</th>
                            <th class="py-2 px-4 bg-gray-100 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Previous Rank</th>
                            <th class="py-2 px-4 bg-gray-100 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider rounded-tr-lg">Change</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        keywords.forEach(keyword => {
            const changeInfo = changeDisplayFunc(keyword);
            sectionHtml += `
                            <tr class="border-b border-gray-200 last:border-b-0">
                                <td class="py-2 px-4 text-sm text-gray-800">${keyword.keyword || 'N/A'}</td>
                                <td class="py-2 px-4 text-sm text-gray-800">${keyword.current_rank || 'N/A'}</td>
                                <td class="py-2 px-4 text-sm text-gray-800">${keyword.previous_rank || 'N/A'}</td>
                                <td class="py-2 px-4 text-sm ${changeInfo.class}">${changeInfo.text}</td>
                            </tr>
                    `;
        });

        sectionHtml += `
                    </tbody>
                </table>
            </div>
        `;
        return sectionHtml;
    };

    const getUpChangeDisplay = (keyword) => {
        const currentRank = parseInt(String(keyword.current_rank).split('/')[0]);
        const previousRank = parseInt(String(keyword.previous_rank).split('/')[0]);
        const diff = previousRank - currentRank;
        return { text: `▲ ${diff}`, class: 'text-green-500 font-medium' };
    };

    const getDownChangeDisplay = (keyword) => {
        const currentRank = parseInt(String(keyword.current_rank).split('/')[0]);
        const previousRank = parseInt(String(keyword.previous_rank).split('/')[0]);
        const diff = currentRank - previousRank;
        return { text: `▼ ${diff}`, class: 'text-gray-500 font-medium' };
    };

    const getNewChangeDisplay = (keyword) => {
        return { text: '▲ New in Top 100', class: 'text-blue-500 font-medium' };
    };

    tableHtml += renderSection('Up-Ranking Keywords', upKeywords, getUpChangeDisplay);
    tableHtml += renderSection('Down-Ranking Keywords', downKeywords, getDownChangeDisplay);
    tableHtml += renderSection('New Keywords', newKeywords, getNewChangeDisplay);

    combinedKeywordsTableContainer.innerHTML = tableHtml;
}