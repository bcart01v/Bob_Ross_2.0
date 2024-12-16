const API_BASE_URL = "http://127.0.0.1:5005";

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

// Photo Analysis
async function analyzePhoto(photoReference) {
    try {
        if (!photoReference) {
            console.warn("Photo reference is null, skipping analysis.");
            return;
        }

        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ photo_reference: photoReference }),
        });

        if (!response.ok) throw new Error("Failed to analyze photo");

        const data = await response.json();
        console.log("Full API response:", data);

        console.log("Analyzed labels:", data.labels);
        console.log("Matched subjects:", data.matched_subjects);
        console.log("Matched episodes:", data.matched_episodes);

        displayResults(data.matched_subjects, data.matched_episodes);
    } catch (error) {
        console.error("Error analyzing photo:", error);
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

// Populate webpage with retrieved data
function displayResults(subjects, episodes) {
    
    console.log("Subjects:", subjects);
    console.log("Episodes:", episodes);

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
                    </li>
                `).join("")}
            </ul>
        `;
        resultsContainer.innerHTML += episodesHTML;
    } else {
        resultsContainer.innerHTML += `<p> No episodes for these given subjects.</p>`;
    }
}