async function loadReviews() {
    const container = document.getElementById("reviews-container");
    container.innerHTML = "<p style='text-align: center; color: #666; margin-top: 30px;'>Loading reviews...</p>";

    const response = await fetchWithAuth("/api/home/", {
        headers: {
            "Content-Type": "application/json"
        }
    });

    if (!response) return; // redirected to login

    if (!response.ok) {
        container.innerHTML = "<p style='text-align: center; color: red;'>Unable to load reviews.</p>";
        return;
    }

    const data = await response.json();
    container.innerHTML = "";

    if (!data || data.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 40px 20px; color: #666;">
                <h3>No reviews yet</h3>
                <p>Be the first reader to share a book review!</p>
                <a href="/form/" style="display: inline-block; margin-top: 10px; background-color: #007bff; color: white; padding: 10px 20px; border-radius: 5px; text-decoration: none;">+ Add Review</a>
            </div>
        `;
        return;
    }

    data.forEach(review => {
        const ratingStars = review.rating ? "⭐".repeat(review.rating) : "";
        const bookTitle = review.book_title || review.book || "Book";
        const authorText = review.author ? `<span style="font-size: 14px; color: #666; font-weight: normal;"> by ${review.author}</span>` : "";

        container.innerHTML += `
            <div class="review-card">
                <h3>${bookTitle}${authorText}</h3>

                ${review.book_photo ?
                    `<img src="${review.book_photo}" alt="${bookTitle}" style="max-height: 220px; width: auto; object-fit: cover; border-radius: 6px; margin: 10px 0;">`
                    : ""
                }

                ${review.rating ? `<p><strong>Rating:</strong> ${ratingStars} (${review.rating}/5)</p>` : ""}

                ${review.book_url ?
                    `<p><strong>Book URL:</strong>
                        <a href="${review.book_url}" target="_blank" rel="noopener noreferrer">
                            ${review.book_url}
                        </a>
                    </p>`
                    : ""
                }

                <p><strong>Review:</strong> ${review.book_review}</p>

                <p><strong>Reviewed By:</strong> <em>${review.user}</em></p>
            </div>
        `;
    });
}

loadReviews();

