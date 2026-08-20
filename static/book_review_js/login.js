function getCSRFToken() {
    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfInput) return csrfInput.value;
    const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
    return cookie ? decodeURIComponent(cookie.split('=')[1]) : '';
}

document.getElementById("loginform").addEventListener("submit", async function (e) {
    e.preventDefault();

    const usernameVal = document.getElementById("username").value.trim();
    const passwordVal = document.getElementById("password").value;
    const errorEl = document.getElementById("error");
    errorEl.innerText = "";

    try {
        const response = await fetch("/api/login/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken()
            },
            credentials: "same-origin",
            body: JSON.stringify({
                email: usernameVal,
                username: usernameVal,
                password: passwordVal
            })
        });

        const data = await response.json();

        if (response.ok) {
            window.location.href = "/home/";
        } else {
            errorEl.innerText = data.error || data.detail || "Login failed. Please check your credentials.";
        }
    } catch (error) {
        errorEl.innerText = "Unable to connect to the server.";
    }
});

