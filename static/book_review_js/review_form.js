// Load books into the dropdown on page load
async function loadBooks() {
    try {
        const response = await fetch("/api/books/", {
            headers: {
                "Content-Type": "application/json"
            }
        });

        if (response.status === 401) {
            const refreshed = await refreshAccessToken();
            if (!refreshed) {
                window.location.href = "/login/";
                return;
            }
        }

        if (!response.ok) {
            document.getElementById("book-select").innerHTML =
                '<option value="">Failed to load books</option>';
            return;
        }

        const books = await response.json();
        const select = document.getElementById("book-select");
        select.innerHTML = '<option value="">Select Book...</option>';

        books.forEach(book => {
            const option = document.createElement("option");
            option.value = book.id;
            option.textContent = `${book.title} (${book.author})`;
            select.appendChild(option);
        });

    } catch (error) {
        document.getElementById("book-select").innerHTML =
            '<option value="">Error loading books</option>';
    }
}

// Handle form submission
document.getElementById("review-form").addEventListener("submit", async function (e) {
    e.preventDefault();

    const formData = new FormData();
    formData.append("book", document.getElementById("book-select").value);
    formData.append("book_photo", document.getElementById("book_photo").files[0]);
    formData.append("book_url", document.getElementById("book_url").value);
    formData.append("rating", document.getElementById("rating").value);
    formData.append("book_review", document.getElementById("book_review").value);

    try {
        const response = await fetch("/api/reviews/", {
            method: "POST",
            body: formData
        });

        if (response.status === 401) {
            const refreshed = await refreshAccessToken();
            if (!refreshed) {
                window.location.href = "/login/";
                return;
            }
        }

        const data = await response.json();

        if (response.ok) {
            alert("Review submitted successfully!");
            window.location.href = "/home/";
        } else {
            // Show validation errors
            const errorMessages = [];
            if (typeof data === 'object') {
                for (const key in data) {
                    if (Array.isArray(data[key])) {
                        errorMessages.push(`${key}: ${data[key].join(", ")}`);
                    }
                }
            }
            document.getElementById("error").innerText =
                errorMessages.length ? errorMessages.join(" | ") : "Failed to submit review.";
        }
    } catch (error) {
        document.getElementById("error").innerText =
            "Unable to connect to the server.";
    }
});

// Load books when page loads
loadBooks();
