async function refreshAccessToken() {

    const refreshToken = localStorage.getItem("refresh_token");

    if (!refreshToken) {
        return false;
    }

    const response = await fetch("/api/token/refresh/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            refresh: refreshToken
        })
    });

    if (!response.ok) {
        return false;
    }

    const data = await response.json();

    localStorage.setItem("access_token", data.access);

    return true;
}