// jwt-manager.js: Manages JWT token lifecycle, auto-refresh, and secure session handling.
//
// This module is critical for maintaining secure user sessions and providing a seamless
// user experience in the dashboard. It handles the automatic refreshing of JWTs (JSON Web Tokens)
// to prevent session expiration and intercepts all fetch requests to ensure tokens are sent
// and refreshed as needed.
//
// Key Aspects:
// - JWTStatusDisplay Class: Provides visual feedback to the user about their session status
//   and warns about impending token expiration.
// - JWTManager Class: Manages the core logic for JWT operations:
//   - Auto-refresh: Periodically attempts to refresh the access token before it expires.
//   - Global Fetch Interceptor: Automatically attaches JWTs to outgoing requests and
//     handles 401 (Unauthorized) responses by attempting a silent token refresh.
//   - CSRF Token Handling: Manages CSRF tokens for enhanced security in POST/PUT/DELETE requests.
//   - Session Expiry Handling: Redirects the user to the login page upon definitive session expiry.
//
// Dependencies:
// - Standard browser Fetch API, setTimeout, setInterval, document.cookie
//
// Key Functions:
// - initializeJwtManager(): The entry point to set up the JWT management system.
// - JWTStatusDisplay.updateStatus(): Fetches user info to update session status display.
// - JWTManager.refreshToken(): Attempts to refresh the JWT token with the backend.
// - JWTManager.setupGlobalFetchInterceptor(): Intercepts fetch requests for token management.
// - JWTManager.getCsrfToken(), JWTManager.getCsrfRefreshToken(): Helper functions to extract CSRF tokens from cookies.

// JWT Status Display: Shows current JWT status and expiration warnings.
class JWTStatusDisplay {
  constructor() {
    this.statusElement = null;
    this.warningElement = null;
    this.init();
  }

  init() {
    this.createStatusBar();
    this.updateStatus();
    setInterval(() => this.updateStatus(), 60000); // Update every minute
  }

  createStatusBar() {
    this.statusElement = document.createElement("div");
    this.statusElement.style.cssText = `
            position: fixed; top: 0; left: 0; right: 0; z-index: 10000;
            background: linear-gradient(90deg, #28a745, #20c997);
            color: white; padding: 8px 20px; font-size: 14px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            display: flex; justify-content: space-between; align-items: center;
        `;
    document.body.appendChild(this.statusElement);
    document.body.style.paddingTop = "50px";
  }

  async updateStatus() {
    try {
      const response = await fetch("/api/user-info", {
        credentials: "same-origin",
      });
      if (response.ok) {
        const data = await response.json();
        const expiresAt = data.token_expires_at * 1000;
        const now = Date.now();
        const remaining = Math.max(0, expiresAt - now);
        const minutes = Math.floor(remaining / 60000);
        this.showSecureStatus(data.username, minutes);
        if (minutes <= 5 && minutes > 0) {
          this.showExpirationWarning(minutes);
        }
      } else {
        this.showInsecureStatus();
      }
    } catch (error) {
      this.showInsecureStatus();
    }
  }

  showSecureStatus(username, minutes) {
    this.statusElement.innerHTML = `
            <div>
                🔒 <strong>Secure Session Active</strong> - Logged in as: ${username}
            </div>
            <div>
                ⏱️ Token expires in: <strong>${minutes} minutes</strong>
                <span style="margin-left: 15px; opacity: 0.8;">Auto-refresh enabled</span>
            </div>
        `;
    this.statusElement.style.background =
      "linear-gradient(90deg, #28a745, #20c997)";
  }

  showInsecureStatus() {
    this.statusElement.innerHTML = `
            <div>⚠️ <strong>Authentication Required</strong></div>
            <div>Please login through WordPress to continue</div>
        `;
    this.statusElement.style.background =
      "linear-gradient(90deg, #dc3545, #fd7e14)";
  }

  showExpirationWarning(minutes) {
    if (this.warningElement) return;
    this.warningElement = document.createElement("div");
    this.warningElement.style.cssText = `
            position: fixed; top: 60px; right: 20px; z-index: 10001;
            background: #fff3cd; border-left: 5px solid #ffc107;
            padding: 15px 20px; border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
            max-width: 400px; font-family: Arial, sans-serif;
        `;
    this.warningElement.innerHTML = `
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <span style="font-size: 24px; margin-right: 10px;">⚠️</span>
                <strong style="color: #856404;">Session Expiring Soon</strong>
                <button onclick="this.parentElement.parentElement.parentElement.remove()" 
                        style="margin-left: auto; background: none; border: none; font-size: 20px; cursor: pointer;">×</button>
            </div>
            <p style="margin: 0; color: #856404; font-size: 14px;">
                Your session will expire in ${minutes} minutes. Don't worry - it will automatically refresh!
            </p>
        `;
    document.body.appendChild(this.warningElement);
    setTimeout(() => {
      if (this.warningElement) {
        this.warningElement.remove();
        this.warningElement = null;
      }
    }, 120000);
  }
}

// jwt-manager.js: Provides utility functions for handling JWT tokens.
class JWTManager {
  constructor() {
    this.refreshInterval = null;
    this.isRefreshing = false; // Prevent duplicate refresh flag
  }

  init() {
    this.setupAutoRefresh();
    this.setupVisibilityChange();
    // --- Global fetch interceptor setup ---
    this.setupGlobalFetchInterceptor();
    console.log(
      "[JWT-MANAGER] Auto token refresh and fetch interceptor initialized"
    );
  }

  // --- Global fetch interceptor setup ---
  setupGlobalFetchInterceptor() {
    const originalFetch = window.fetch;
    const self = this;

    window.fetch = async function (url, options) {
      // Ensure options object exists
      if (!options) {
        options = {};
      }

      // Always include credentials
      if (!options.credentials) {
        options.credentials = "same-origin";
      }

      // CSRF token auto-adding logic
      const method = options?.method?.toUpperCase() || "GET";
      if (["POST", "PUT", "PATCH", "DELETE"].includes(method) && !url.includes('/api/token/refresh')) {
        if (!options.headers) {
          options.headers = {};
        }

        // Content-Type setting
        if (!options.headers["Content-Type"]) {
          options.headers["Content-Type"] = "application/json";
        }

        if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
          console.log("[CSRF DEBUG] All Cookies:", document.cookie);
        }
        const csrfToken = self.getCsrfToken();
        if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
          console.log("[CSRF DEBUG] Extracted CSRF Token:", csrfToken);
        }

        if (csrfToken) {
          if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
            console.log("[CSRF DEBUG] CSRF Token found. Adding to header.");
          }
          options.headers["X-CSRF-TOKEN"] = csrfToken;
        } else {
          if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
            console.warn("[CSRF DEBUG] CSRF Token NOT found in cookies.");
          }

          // Show warning in production if CSRF token is missing
          if (
            window.location.hostname !== "localhost" &&
            window.location.hostname !== "127.0.0.1"
          ) {
            console.error(
              "[CSRF ERROR] Production environment requires CSRF token for secure requests"
            );
          }
        }
      }

      // Only show debug logs in a non-production environment
      if (window.APP_CONTEXT && window.APP_CONTEXT.userInfo && window.APP_CONTEXT.userInfo.FLASK_ENV === 'development') {
          console.log("[FETCH DEBUG] Final request options:", options);
      }
      let response = await originalFetch(url, options);

      // 401 Unauthorized handling
      if (
        response.status === 401 &&
        !(options && options._retry) &&
        !url.includes("/api/token/refresh")
      ) {
        console.log(
          `[INTERCEPTOR] API call to ${url} failed with 401. Attempting silent refresh.`
        );

        const refreshSuccessful = await self.refreshToken();

        if (refreshSuccessful) {
                    console.log('[INTERCEPTOR] Silent refresh successful. Retrying original request.');
                    // --- Short delay added (wait for cookie update) ---
                    await new Promise(resolve => setTimeout(resolve, 300)); // 300ms delay

                    // Retry the original request (with retry flag and explicit credentials)
                    const newOptions = { ...options, _retry: true, credentials: 'same-origin' };
                    return originalFetch(url, newOptions);
                } else {
          console.error(
            "[INTERCEPTOR] Silent refresh failed. Session is truly expired."
          );
          self.handleFinalExpiry();
        }
      }
      return response;
    };
  }

  setupAutoRefresh() {
    this.refreshInterval = setInterval(() => this.refreshToken(), 1200000); // Update every 20 minutes
    setTimeout(() => this.refreshToken(), 300000); // First attempt after 5 minutes
  }

  setupVisibilityChange() {
    document.addEventListener("visibilitychange", () => {
      if (!document.hidden) {
        this.refreshToken();
      }
    });
  }

  // --- Return success/failure status ---
  async refreshToken() {
    if (this.isRefreshing) {
      console.log("[JWT-MANAGER] Refresh already in progress. Skipping.");
      return false; 
    }
    this.isRefreshing = true;

    try {
      const response = await fetch('/api/token/refresh', {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-TOKEN': this.getCsrfRefreshToken() // Use refresh token's CSRF
                }
            });

      if (response.ok) {
        console.log("[JWT-MANAGER] Token refreshed successfully");
        this.showRefreshNotification();
        return true;
      } else {
        console.warn(
          "[JWT-MANAGER] Token refresh failed with status:",
          response.status
        );

        // 403 CSRF token validation failure
        if (response.status === 403) {
          console.error(
            "[JWT-MANAGER] CSRF token validation failed during refresh"
          );
        }

        return false;
      }
    } catch (error) {
      console.error("[JWT-MANAGER] Network error during token refresh:", error);
      return false;
    } finally {
      this.isRefreshing = false;
    }
  }

  // --- Helper function to read CSRF token from cookies ---
  getCsrfToken() {
    if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
      console.log("[CSRF DEBUG] All cookies when getting access token CSRF:", document.cookie);
    }
    const cookies = document.cookie.split(";");
    for (let cookie of cookies) {
      const [name, value] = cookie.trim().split("=");
      if (name === "csrf_access_token") {
        return decodeURIComponent(value);
      }
    }
    if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
      console.warn("[CSRF DEBUG] No csrf_access_token found in cookies");
    }
    return null;
  }

  // --- Helper function to read Refresh CSRF token from cookies ---
  getCsrfRefreshToken() {
    if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
      console.log("[CSRF DEBUG] All cookies when getting refresh token CSRF:", document.cookie);
    }
    const cookies = document.cookie.split(";");
    for (let cookie of cookies) {
      const [name, value] = cookie.trim().split("=");
      if (name === "csrf_refresh_token") {
        if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
          console.log("[CSRF DEBUG] Found Refresh CSRF token:", value);
        }
        return decodeURIComponent(value);
      }
    }
    if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
      console.warn("[CSRF DEBUG] No Refresh CSRF token found in cookies");
    }
    return null;
  }

  showRefreshNotification() {
    const notification = document.createElement("div");
    notification.style.cssText = `
            position: fixed; bottom: 20px; right: 20px; z-index: 10001;
            background: #d4edda; border: 1px solid #c3e6cb;
            color: #155724; padding: 12px 20px; border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            font-family: Arial, sans-serif; font-size: 14px;
        `;
    notification.innerHTML = `✅ <strong>Security Update:</strong> Session automatically extended`;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
  }

  // --- Final expiry handler ---
  handleFinalExpiry() {
    console.log(
      "[JWT-MANAGER] Final expiry handler triggered. Redirecting to login."
    );
    // Stop automatic refresh
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
    // Redirect to login page as a last resort
    window.location.href = "https://gnaemarketing.com.au/report/wp-admin";
  }

  destroy() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
    // --- Restore interceptor (if necessary) ---
    // window.fetch = originalFetch; 
    console.log("[JWT-MANAGER] Destroyed");
  }
}

export function initializeJwtManager() {
  if (window.jwtManager) {
    console.log("[APP] JWT security system already initialized.");
    return;
  }
  window.jwtStatusDisplay = new JWTStatusDisplay();
  window.jwtManager = new JWTManager();
  window.jwtManager.init(); // Call init to setup interceptors and auto-refresh
  console.log("[APP] JWT security system initialized");

  window.addEventListener("beforeunload", () => {
    if (window.jwtManager) {
      window.jwtManager.destroy();
    }
  });
}