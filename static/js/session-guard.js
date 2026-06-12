// session-guard.js: JWT-based session management and UI notifications.
//
// This module implements a client-side session management system that monitors
// the JWT (JSON Web Token) expiration and provides visual feedback and actions
// to the user. It aims to enhance user experience by preventing abrupt session
// expirations and guiding users through re-authentication when necessary.
//
// Key Aspects:
// - Periodically checks the JWT expiration time.
// - Displays warning toasts when the session is about to expire.
// - Attempts to silently refresh the token if expiration is imminent.
// - Shows a modal dialog and redirects to the WordPress login page if the session fully expires.
// - Integrates with the application context to disable itself in development mode.
//
// Dependencies:
// - Standard browser Fetch API, setTimeout, setInterval, document.cookie
// - window.APP_CONTEXT (injected from Flask backend)
//
// Key Functions:
// - init(): Initializes the session guard, adds CSS styles, and sets up periodic checks.
// - showWarningToast(message): Displays a temporary warning notification.
// - showExpiredModal(): Displays a persistent modal indicating session expiration.
// - getTokenExpiration(): Fetches the token expiration time from the backend.
// - refreshToken(): Attempts to refresh the JWT token.
// - checkTokenStatus(): The core logic for monitoring token status and triggering actions.
// - setupPeriodicCheck(): Sets up the interval for checking token status.

class SessionGuard {
    constructor() {
        this.warningElement = null;
        this.checkInterval = null;
        this.isModalOpen = false;
        this.tokenRefreshAttempted = false;
        this.init();
    }

    init() {
        this.addStyles();
        if (window.APP_CONTEXT && window.APP_CONTEXT.userInfo && window.APP_CONTEXT.userInfo.FLASK_ENV === 'development') {
            console.log('[SESSION-GUARD] Development mode detected. Session guard disabled.');
            return;
        }
        this.setupPeriodicCheck();
        console.log('[SESSION-GUARD] JWT session management active');
    }

    addStyles() {
        if (document.getElementById('session-guard-styles')) return;
        const styles = document.createElement('style');
        styles.id = 'session-guard-styles';
        styles.textContent = `
            @keyframes slideInRight { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
            @keyframes slideOutRight { from { transform: translateX(0); opacity: 1; } to { transform: translateX(100%); opacity: 0; } }
            .session-modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); z-index: 10000; display: flex; align-items: center; justify-content: center; }
            .session-warning-toast { position: fixed; top: 20px; right: 20px; background: #fff3cd; border-left: 5px solid #ffeaa7; padding: 16px 20px; border-radius: 8px; z-index: 9999; box-shadow: 0 8px 25px rgba(0,0,0,0.15); max-width: 400px; font-family: 'Inter', sans-serif; animation: slideInRight 0.4s ease-out; }
            .toast-header { display: flex; align-items: center; margin-bottom: 12px; }
            .toast-icon { font-size: 24px; margin-right: 12px; }
            .toast-title { color: #856404; font-size: 16px; font-weight: 600; }
            .toast-close-btn { margin-left: auto; background: none; border: none; font-size: 24px; cursor: pointer; color: #856404; opacity: 0.7; }
            .toast-message { margin: 0; color: #856404; font-size: 14px; line-height: 1.5; }
        `;
        document.head.appendChild(styles);
    }

    showWarningToast(message) {
        if (this.warningElement) this.closeWarningToast();

        this.warningElement = document.createElement('div');
        this.warningElement.className = `session-warning-toast`;
        this.warningElement.innerHTML = `
            <div class="toast-header">
                <span class="toast-icon">⚠️</span>
                <strong class="toast-title">Session Warning</strong>
                <button class="toast-close-btn">&times;</button>
            </div>
            <p class="toast-message">${message}</p>
        `;

        document.body.appendChild(this.warningElement);
        this.warningElement.querySelector('.toast-close-btn').onclick = () => this.closeWarningToast();
        setTimeout(() => this.closeWarningToast(), 10000);
    }

    closeWarningToast() {
        if (!this.warningElement) return;
        this.warningElement.style.animation = 'slideOutRight 0.4s ease-out forwards';
        setTimeout(() => {
            this.warningElement?.remove();
            this.warningElement = null;
        }, 400);
    }

    showExpiredModal() {
        if (this.isModalOpen) return;
        this.isModalOpen = true;
        this.closeWarningToast();

        const modal = document.createElement('div');
        modal.className = 'session-modal-overlay';
        modal.innerHTML = `
            <div style="background: white; padding: 30px; border-radius: 16px; box-shadow: 0 20px 50px rgba(0,0,0,0.3); max-width: 500px; text-align: center; font-family: 'Inter', sans-serif;">
                <div style="font-size: 48px; margin-bottom: 16px;">⌛</div>
                <h2 style="color: #ef4444; margin-bottom: 16px; font-size: 24px;">Session Expired</h2>
                <p style="color: #374151; margin-bottom: 24px; line-height: 1.6;">
                    Your session has expired. Please log in again through WordPress.
                </p>
                <button onclick="window.location.href='https://gnaemarketing.com.au/report/wp-admin'" style="background: #21759b; color: white; padding: 12px 24px; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer;">Login to WordPress</button>
            </div>
        `;
        document.body.appendChild(modal);
        if (this.checkInterval) clearInterval(this.checkInterval);
    }

    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }

    async getTokenExpiration() {
        try {
            const response = await fetch("/api/user-info", {
                credentials: "same-origin",
            });
            if (response.ok) {
                const responseText = await response.text();
                if (!responseText) {
                    console.warn('[SESSION-GUARD] /api/user-info returned an empty response. Assuming no session.');
                    return null;
                }
                const data = JSON.parse(responseText);
                if (data && data.token_expires_at) {
                    return data.token_expires_at * 1000; // Convert to milliseconds
                } else {
                    console.warn('[SESSION-GUARD] /api/user-info response is missing token_expires_at.');
                    return null;
                }
            } else {
                console.warn('[SESSION-GUARD] Failed to fetch user info for token expiration. Status:', response.status);
                return null;
            }
        } catch (error) {
            console.error('[SESSION-GUARD] Error fetching user info for token expiration:', error);
            return null;
        }
    }

    async refreshToken() {
        console.log('[SESSION-GUARD] Attempting to refresh token...');
        try {
            const response = await fetch('/api/token/refresh', {
                method: 'POST',
                headers: { 'Accept': 'application/json' },
                credentials: 'same-origin'
            });

            if (response.ok) {
                console.log('[SESSION-GUARD] Token refreshed successfully.');
                this.tokenRefreshAttempted = false; // Reset for the new token
                this.closeWarningToast();
                return true;
            } else {
                console.error('[SESSION-GUARD] Failed to refresh token.');
                return false;
            }
        } catch (error) {
            console.error('[SESSION-GUARD] Error refreshing token:', error);
            return false;
        }
    }

    async checkTokenStatus() {
        const expirationTime = await this.getTokenExpiration();
        if (!expirationTime) {
            // This now correctly handles cases where the token is missing, invalid, or the API fails.
            // We should only show the modal if a token was previously present, indicating a real session expiration.
            // A simple proxy for this is to check if the modal is already open.
            // If there's no token from the start, we don't want to flash an "expired" modal at a new user.
            // The logic inside showExpiredModal already prevents it from opening twice.
            // Let's call it, but only if a refresh hasn't just been attempted.
            if (!this.tokenRefreshAttempted) {
                 this.showExpiredModal();
            }
            return;
        }

        const now = Date.now();
        const remaining = expirationTime - now;
        const remainingSeconds = Math.round(remaining / 1000);

        // If less than 2 minutes remaining, show warning
        if (remainingSeconds <= 120 && remainingSeconds > 60) {
            this.showWarningToast(`Your session will expire in about ${Math.ceil(remainingSeconds / 60)} minutes.`);
        }

        // If less than 60 seconds remaining, try to refresh
        if (remainingSeconds > 0 && remainingSeconds <= 60 && !this.tokenRefreshAttempted) {
            this.tokenRefreshAttempted = true;
            const refreshed = await this.refreshToken();
            if (!refreshed) {
                this.showExpiredModal();
            }
        }

        // If token is expired
        if (remaining <= 0) {
            this.showExpiredModal();
        }
    }

    setupPeriodicCheck() {
        // Check every 30 seconds
        this.checkInterval = setInterval(() => this.checkTokenStatus(), 30000);
    }

    destroy() {
        if (this.checkInterval) clearInterval(this.checkInterval);
        this.closeWarningToast();
        console.log('[SESSION-GUARD] Destroyed');
    }
}

// Initialize the session guard
window.sessionGuard = new SessionGuard();
