async function loadProfile() {

    let token = localStorage.getItem("access_token");

    if (!token) {
        window.location.href = "/login/";
        return;
    }

    let response = await fetch("/api/profile/", {
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });

    if (response.status === 401) {

        const refreshed = await refreshAccessToken();

        if (!refreshed) {
            localStorage.clear();
            window.location.href = "/login/";
            return;
        }

        token = localStorage.getItem("access_token");

        response = await fetch("/api/profile/", {
            headers: {
                "Authorization": `Bearer ${token}`
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

