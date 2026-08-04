async function refreshAccessToken() {

    // The refresh token is stored in an HttpOnly cookie, automatically sent with requests.
    // The backend's cookie-refresh endpoint handles reading it from the cookie.
    const response = await fetch("/api/token/cookie-refresh/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        }
    });

    if (!response.ok) {
        return false;
    }

    // New access token is set as HttpOnly cookie by the backend
    return true;
}

// Shared fetch helper - handles the full "token expired" flow:
// 1. On 401, try to refresh the access token via the refresh cookie.
// 2. If refresh succeeds, retry the original request once.
// 3. If refresh fails (token truly expired), redirect to login page.
// Returns the last Response, or null if redirected to login.
async function fetchWithAuth(url, options = {}) {
    let response = await fetch(url, options);

    if (response.status === 401) {
        const refreshed = await refreshAccessToken();

        if (!refreshed) {
            window.location.href = "/login/";
            return null;
        }

        // Retry with new access token (automatically sent via cookie)
        response = await fetch(url, options);
    }

    return response;
}
