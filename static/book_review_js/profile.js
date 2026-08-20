async function loadProfile() {
    const response = await fetchWithAuth("/api/profile/", {
        headers: {
            "Content-Type": "application/json"
        }
    });

    if (!response) return;

    if (!response.ok) {
        window.location.href = "/login/";
        return;
    }

    const data = await response.json();

    const usernameEl = document.getElementById("username");
    const emailEl = document.getElementById("email");
    const dateJoinedEl = document.getElementById("date_joined");
    const reviewsCountEl = document.getElementById("reviews_count");

    if (usernameEl) usernameEl.textContent = data.user_name || data.username || "N/A";
    if (emailEl) emailEl.textContent = data.email || "N/A";
    if (dateJoinedEl) {
        dateJoinedEl.textContent = data.date_joined ? new Date(data.date_joined).toLocaleDateString() : "N/A";
    }
    if (reviewsCountEl) {
        reviewsCountEl.textContent = data.reviews_count !== undefined ? data.reviews_count : 0;
    }
}

loadProfile();

