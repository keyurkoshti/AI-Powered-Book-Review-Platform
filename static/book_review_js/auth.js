async function refreshAccessToken() {
    const response = await fetch("/api/token/cookie-refresh/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        }
    });

    if (!response.ok) {
        return false;
    }
    return true;
}

async function fetchWithAuth(url, options = {}) {
    let response = await fetch(url, options);

    if (response.status === 401) {
        const refreshed = await refreshAccessToken();

        if (!refreshed) {
            window.location.href = "/login/";
            return null;
        }
        response = await fetch(url, options);
    }

    return response;
}
