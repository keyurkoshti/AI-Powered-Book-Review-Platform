async function loadReviews() {

    let token = localStorage.getItem("access_token");

    if (!token) {
        window.location.href = "/login/";
        return;
    }

    let response = await fetch("/api/home/", {
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });

    // Access token expired
    if (response.status === 401) {

        const refreshed = await refreshAccessToken();

        if (!refreshed) {
            localStorage.clear();
            window.location.href = "/login/";
            return;
        }

        token = localStorage.getItem("access_token");

        // Retry request with new token
        response = await fetch("/api/home/", {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });
    }

    if (!response.ok) {
        alert("Unable to load reviews.");
        return;
    }

    const data = await response.json();

    const container = document.getElementById("reviews-container");

    container.innerHTML = "";

    data.forEach(review => {

        container.innerHTML += `
            <div class="review-card">
                <h3>${review.book}</h3>

                ${review.book_photo ?
                    `<img src="${review.book_photo}" width="150">`
                    : ""
                }

                <p><strong>Book URL:</strong>
                    <a href="${review.book_url}" target="_blank">
                        ${review.book_url}
                    </a>
                </p>

                <p><strong>Review:</strong> ${review.book_review}</p>

                <p><strong>Reviewed By:</strong> ${review.user}</p>

                <hr>
            </div>
        `;
    });
}

loadReviews();