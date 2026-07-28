function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

// Toast notification function
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
        showToast('✅ Registration successful!', 'success');
        setTimeout(() => {
            window.location.href = "/login/";
        }, 1500);
    }
    else {
        const parts = [];
        if (data.error) parts.push(data.error);
        if (data.username) parts.push(data.username);
        if (data.email) parts.push(data.email);
        if (data.password) parts.push(data.password);
        if (data.password1) parts.push(data.password1);
        if (data.password2) parts.push(data.password2);

        const errorMsg = parts.length ? parts.join(" ") : "something went wrong";
        showToast('❌ ' + errorMsg, 'error');
        document.getElementById('error').innerText = errorMsg;
    }
});

