document.getElementById("logout-btn").addEventListener("click", async function () {

    await fetch("/api/logout/", {
        method: "POST"
    });

    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");

    window.location.href = "/login/";
});