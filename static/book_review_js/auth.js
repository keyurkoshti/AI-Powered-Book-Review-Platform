function getCSRFToken() {
    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfInput) return csrfInput.value;
    const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
    return cookie ? decodeURIComponent(cookie.split('=')[1]) : '';
}

async function refreshAccessToken() {
    try {
        const response = await fetch("/api/token/cookie-refresh/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken()
            },
            credentials: "same-origin"
        });

        if (!response.ok) {
            return false;
        }
        return true;
    } catch (err) {
        return false;
    }
}

async function fetchWithAuth(url, options = {}) {
    options.credentials = options.credentials || "same-origin";
    
    let response;
    try {
        response = await fetch(url, options);
    } catch (err) {
        console.error("Network error:", err);
        return null;
    }

    if (response.status === 401) {
        const refreshed = await refreshAccessToken();

        if (!refreshed) {
            window.location.href = "/login/";
            return null;
        }
        
        try {
            response = await fetch(url, options);
        } catch (err) {
            console.error("Network error on retry:", err);
            return null;
        }
    }

    return response;
}

