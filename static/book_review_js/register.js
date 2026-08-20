function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

function showToast(message, type = 'success') {
    // Remove existing toast if any
    const existing = document.querySelector('.toast-notification');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'toast-notification';
    toast.textContent = message;
    
    const bgColor = type === 'success' ? '#4CAF50' : '#f44336';
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${bgColor};
        color: white;
        padding: 16px 24px;
        border-radius: 8px;
        font-size: 15px;
        font-family: Arial, sans-serif;
        box-shadow: 0 4px 14px rgba(0,0,0,0.2);
        z-index: 9999;
        opacity: 0;
        transform: translateX(100%);
        transition: all 0.4s ease;
    `;
    document.body.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateX(0)';
    });

    // Auto remove after 3 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 400);
    }, 3000);
}

document.getElementById('registerform').addEventListener("submit", async function(event) {
    event.preventDefault(); 

    const usernameVal = document.getElementById('username').value.trim();
    const emailVal = document.getElementById('email').value.trim();
    const passwordVal = document.getElementById('password').value;

    try {
        const response = await fetch('/api/register/', {
            method : "POST",
            headers : {
                "Content-Type" : "application/json",
                "X-CSRFToken" : getCSRFToken()
            },
            body: JSON.stringify({
                user_name : usernameVal,
                username : usernameVal,
                email: emailVal,
                password: passwordVal,
            })
        });

        const data = await response.json();

        if (response.ok){
            showToast('✅ Registration successful! Redirecting to login...', 'success');
            setTimeout(() => {
                window.location.href = "/login/";
            }, 1200);
        }
        else {
            const parts = [];
            if (typeof data === 'string') {
                parts.push(data);
            } else if (typeof data === 'object') {
                for (const key in data) {
                    if (Array.isArray(data[key])) {
                        parts.push(`${data[key].join(", ")}`);
                    } else if (typeof data[key] === 'string') {
                        parts.push(data[key]);
                    }
                }
            }

            const errorMsg = parts.length ? parts.join(" ") : "Something went wrong during registration.";
            showToast('❌ ' + errorMsg, 'error');
            document.getElementById('error').innerText = errorMsg;
        }
    } catch (err) {
        showToast('❌ Unable to connect to server.', 'error');
        document.getElementById('error').innerText = "Unable to connect to the server.";
    }
});

