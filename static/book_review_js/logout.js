document.getElementById("logout-btn").addEventListener("click", async function () {

    await fetch("/api/logout/", {
        method: "POST"
    });

    // Cookies are cleared by the backend on logout
    window.location.href = "/login/";
});
