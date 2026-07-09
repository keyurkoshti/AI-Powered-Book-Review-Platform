function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

document.getElementById('registerform').addEventListener("submit", async function(event) {
    event.preventDefault(); 

    const response = await fetch('/api/register',{
        method : "POST",
        headers : {
            "content-type" : "application/json",
            "X-CSRFToken" : getCSRFToken()
        },
        body: JSON.stringify({
            username : document.getElementById('username').value,
            email: document.getElementById('email').value,
            password1: document.getElementById('password1').value,
            password2: document.getElementById('password2').value,
        })
    });

    const data = await response.json()

    if (response.ok){
        alert("registration successful");
        window.location.href = "/login/";
    }
    else {
        const parts = [];
        if (data.error) parts.push(data.error);
        if (data.username) parts.push(data.username);
        if (data.email) parts.push(data.email);
        if (data.password) parts.push(data.password);
        if (data.password1) parts.push(data.password1);
        if (data.password2) parts.push(data.password2);

        document.getElementById('error').innerText = parts.length ? parts.join(" ") : "something went wrong";
    }
});

