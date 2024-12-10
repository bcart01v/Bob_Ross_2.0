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
            <img src="${photoUrl}" class="d-block w-100" alt="${photo.name}">
            <div class="carousel-caption d-md-block">
                <h5>${photo.name}</h5>
                <p>${photo.location || "Location unavailable"}</p>
            </div>
        `;
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

// Dropdown logic
document.addEventListener("DOMContentLoaded", () => {
    const dropdown = document.getElementById("countryDropdown");

    dropdown.addEventListener("change", () => {
        const region = dropdown.value;
        if (region) {
            fetchNaturePhotos(region);
        }
    });
});