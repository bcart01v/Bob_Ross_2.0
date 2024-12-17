const API_BASE_URL = "http://127.0.0.1:5005";

let currentPage = 1;
const pageSize = 10;

// Get the Photos
async function fetchNaturePhotos(region) {
    try {
        const response = await fetch(`${API_BASE_URL}/places?region=${region}`);
        if (!response.ok) throw new Error("Failed to fetch places");

        const places = await response.json();
        populateCarousel(places);
    } catch (error) {
        console.error("Error fetching nature photos:", error);
    }
}

// Display the Photos
function populateCarousel(photos) {
    const carouselContent = document.getElementById("carouselContent");
    carouselContent.innerHTML = "";

    photos.slice(0, 10).forEach((photo, index) => {
        const isActive = index === 0 ? "active" : "";
        const photoUrl = `${API_BASE_URL}/photo?photo_reference=${photo.photo_reference}`;

        const carouselItem = document.createElement("div");
        carouselItem.className = `carousel-item ${isActive}`;
        carouselItem.innerHTML = `
            <img src="${photoUrl}" class="d-block w-100" alt="${photo.name}" data-photo-reference="${photo.photo_reference}">
            <div class="carousel-caption d-md-block">
                <h5 class="photo-name">${photo.name}</h5>
                <p class="photo-location">${photo.location || "Location unavailable"}</p>
            </div>
        `;

        // Click event to return info
        const imgElement = carouselItem.querySelector("img");
        imgElement.addEventListener("click", () => analyzePhoto(photo.photo_reference));

        carouselContent.appendChild(carouselItem);
    });

    if (!photos.length) {
        carouselContent.innerHTML = `
            <div class="carousel-item active">
                <div class="d-flex justify-content-center align-items-center" style="height: 300px;">
                    <h5>No photos available for this region</h5>
                </div>
            </div>
        `;
    }
}

async function fetchPaginatedEpisodes(photoReference) {
    try {
        const response = await fetch(`${API_BASE_URL}/analyze?page=${currentPage}&page_size=${pageSize}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ photo_reference: photoReference }),
        });

        if (!response.ok) throw new Error("Failed to fetch paginated results");

        const data = await response.json();

        if (!data.pagination) {
            console.error("Pagination data missing in API response");
            return;
        }

        displayResults(data.matched_subjects, data.matched_episodes, data.pagination, photoReference);
    } catch (error) {
        console.error("Error fetching paginated results:", error);
    }
}

// Photo Analysis
async function analyzePhoto(photoReference) {
    try {
        if (!photoReference) {
            console.warn("Photo reference is null, skipping analysis.");
            return;
        }

        currentPage = 1;
        fetchPaginatedEpisodes(photoReference);
    } catch (error) {
        console.error("Error analyzing photo:", error);
    }
}

// Populate webpage with retrieved data
function displayResults(subjects, episodes, pagination, photoReference) {
    console.log("Subjects:", subjects);
    console.log("Episodes:", episodes);
    console.log("Pagination Info:", pagination);

    const resultsContainer = document.getElementById("resultsContainer");

    // Clear previous results
    resultsContainer.innerHTML = "";

    // Display matched episodes
    if (episodes.length > 0) {
        const episodesHTML = `
            <h3>Recommended Episodes:</h3>
            <ul>
                ${episodes.map(episode => `
                    <li>
                        <strong>${episode.season_episode} - ${episode.title}</strong>
                        ${episode.youtube_link ? `<br><a href="${episode.youtube_link}" target="_blank">Watch on YouTube</a>` : ""}
                    </li>
                `).join("")}
            </ul>
        `;
        resultsContainer.innerHTML += episodesHTML;
    } else {
        resultsContainer.innerHTML += `<p>No episodes for these given subjects.</p>`;
    }

    if (pagination) {
        const paginationControls = `
        <div>
            <button onclick="changePage(${pagination.current_page - 1}, '${photoReference}')"
                ${pagination.current_page === 1 ? "disabled" : ""}>
                Previous
            </button>
            Page ${pagination.current_page} of ${pagination.total_pages}
            <button onclick="changePage(${pagination.current_page + 1}, '${photoReference}')"
                ${pagination.current_page >= pagination.total_pages ? "disabled" : ""}>
                Next
            </button>
        </div>
        `;
    resultsContainer.innerHTML += paginationControls;
    }
}

function changePage(newPage, photoReference) {
    if (newPage > 0) {
        currentPage = newPage;
        fetchPaginatedEpisodes(photoReference);
    }
}

// Dropdown logic
document.addEventListener("DOMContentLoaded", () => {
    const dropdown = document.getElementById("countryDropdown");
    const resultsContainer = document.getElementById("resultsContainer");
    const subheaderText = document.getElementById("subheaderText");
    const carousel = document.getElementById("natureCarousel");

    dropdown.addEventListener("change", () => {
        const region = dropdown.value;

        if (region) {
            resultsContainer.style.display = "block";
            subheaderText.style.display = "block";
            fetchNaturePhotos(region);
        } else {
            resultsContainer.style.display = "none";
            subheaderText.style.display = "none";
            resultsContainer.innerHTML = "";
        }
    });

    // Clear results when carousel moves to new image
    carousel.addEventListener("slide.bs.carousel", () => {
        resultsContainer.innerHTML = "";
    });
});

