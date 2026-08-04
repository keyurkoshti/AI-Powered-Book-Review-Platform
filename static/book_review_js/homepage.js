async function loadReviews() {

    const response = await fetchWithAuth("/api/home/", {
        headers: {
            "Content-Type": "application/json"
        }
    });

    if (!response) return; // redirected to login

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
