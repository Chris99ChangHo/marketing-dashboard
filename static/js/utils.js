// utils.js: Contains common utility functions for the frontend.
//
// This module provides a collection of reusable utility functions that are
// commonly needed across various parts of the frontend JavaScript code.
// These functions aim to simplify common tasks, improve code readability,
// and promote consistency.
//
// Key Aspects:
// - Provides helper functions for data manipulation and formatting.
// - Designed to be imported and used by other frontend modules.
//
// Dependencies:
// - None (relies on standard JavaScript built-in functions)
//
// Key Functions:
// - safeParseFloat(text): Safely converts a string to a floating-point number,
//   handling various non-numeric inputs and returning 0 for invalid values.
// - formatDate(date): Formats a Date object into a 'YYYY-MM-DD' string.

export function safeParseFloat(text) {
    if (typeof text !== 'string' || text.trim() === '' || text.trim().toLowerCase() === 'n/a') {
        return 0;
    }
    const parsed = parseFloat(text.replace(/,/g, '').replace('%', '').replace('s', ''));
    return isNaN(parsed) ? 0 : parsed;
}

export function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}