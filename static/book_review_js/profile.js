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

    document.getElementById("username").textContent = data.username;
    document.getElementById("email").textContent = data.email;
    document.getElementById("date_joined").textContent =
        new Date(data.date_joined).toLocaleDateString();

    document.getElementById("reviews_count").textContent =
        data.reviews_count;
}

loadProfile();
