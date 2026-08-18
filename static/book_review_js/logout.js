document.getElementById("logout-btn").addEventListener("click", async function () {

    await fetch("/api/logout/", {
        method: "POST"
    });
    window.location.href = "/login/";
});
