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
