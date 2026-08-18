
async function loadCategories() {
    try {
        const response = await fetchWithAuth("/api/categories/", {
            headers: {
                "Content-Type": "application/json"
            }
        });

        if (!response) return; 

        if (!response.ok) {
            return;
        }

        const categories = await response.json();
        const categoryInput = document.getElementById("category");

        let datalist = document.getElementById("category-list");
        if (!datalist) {
            datalist = document.createElement("datalist");
            datalist.id = "category-list";
            categoryInput.setAttribute("list", "category-list");
            categoryInput.parentNode.appendChild(datalist);
        }

        datalist.innerHTML = "";
        categories.forEach(cat => {
            const option = document.createElement("option");
            option.value = cat.name;
            datalist.appendChild(option);
        });

    } catch (error) {
        console.error("Failed to load categories:", error);
    }
}

// Handle form submission
document.getElementById("add-book-form").addEventListener("submit", async function (e) {
    e.preventDefault();

const formData = {
        title: document.getElementById("title").value,
        category_name: document.getElementById("category").value,
        author: document.getElementById("author").value,
        description: document.getElementById("description").value
    };

    try {
        const response = await fetchWithAuth("/api/add-book/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(formData)
        });

        if (!response) return; // redirected to login

        const data = await response.json();
        if (response.ok) {
            alert("Book added successfully!");
            window.location.href = "/form/";
        } else {
            const errorMessages = [];
            if (typeof data === 'object') {
                for (const key in data) {
                    if (Array.isArray(data[key])) {
                        errorMessages.push(`${key}: ${data[key].join(", ")}`);
                    }
                }
            }
            document.getElementById("error").innerText =
                errorMessages.length ? errorMessages.join(" | ") : "Failed to add book.";
        }
    } catch (error) {
        document.getElementById("error").innerText = "Unable to connect to the server.";
    }
});

// Load categories when page loads
loadCategories();
