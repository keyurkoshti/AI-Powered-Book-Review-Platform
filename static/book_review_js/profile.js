async function loadProfile() {

    let response = await fetch("/api/profile/", {
        headers: {
            "Content-Type": "application/json"
        }
    });

    if (response.status === 401) {

        const refreshed = await refreshAccessToken();

        if (!refreshed) {
            window.location.href = "/login/";
            return;
        }

        // Retry request with new token (automatically sent via cookie)
        response = await fetch("/api/profile/", {
            headers: {
                "Content-Type": "application/json"
            }
        });
    }

    const data = await response.json();

    document.getElementById("username").textContent = data.username;
    document.getElementById("email").textContent = data.email;
    document.getElementById("date_joined").textContent =
        new Date(data.date_joined).toLocaleDateString();

    document.getElementById("reviews_count").textContent =
        data.reviews_count;
}

loadProfile();
