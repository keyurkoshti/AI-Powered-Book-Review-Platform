document.getElementById("loginform").addEventListener("submit", async function (e) {
    e.preventDefault();

    try {
        const response = await fetch("/api/login/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                username: document.getElementById("username").value,
                password: document.getElementById("password").value
            })
        });

        const data = await response.json();

        if (response.ok) {
            window.location.href = "/home/";
        } else {
            document.getElementById("error").innerText =
                data.error || "Login failed.";
        }
    } catch (error) {
        document.getElementById("error").innerText =
            "Unable to connect to the server.";
    }
});
