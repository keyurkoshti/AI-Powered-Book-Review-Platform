const logoutBtn = document.getElementById("logout-btn");
if (logoutBtn) {
    logoutBtn.addEventListener("click", async function () {
        try {
            await fetch("/api/logout/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": typeof getCSRFToken === 'function' ? getCSRFToken() : ''
                },
                credentials: "same-origin"
            });
        } catch (err) {
            console.error("Logout error:", err);
        }
        window.location.href = "/login/";
    });
}

