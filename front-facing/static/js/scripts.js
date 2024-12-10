document.addEventListener("DOMContentLoaded", async () => {
    const API_URL = "http://127.0.0.1:5005/episodes";
    const episodesTableBody = document.getElementById("episodes-table-body");
    const filterForm = document.getElementById("filter-form");

    // Function to fetch and populate episodes
    async function fetchEpisodes(params = {}) {
        try {
            // Build query parameters
            const query = new URLSearchParams(params).toString();
            const response = await fetch(`${API_URL}?${query}`);

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            const data = await response.json();
            renderEpisodes(data.episodes);
        } catch (error) {
            console.error("Error fetching episodes:", error);
        }
    }

    // Function to render episodes in the table
    function renderEpisodes(episodes) {
        episodesTableBody.innerHTML = ""; // Clear existing rows
        episodes.forEach((episode) => {
            const row = document.createElement("tr");

            const idCell = document.createElement("td");
            idCell.textContent = episode.episode_id;

            const titleCell = document.createElement("td");
            titleCell.textContent = episode.title;

            const airDateCell = document.createElement("td");
            airDateCell.textContent = episode.air_date;

            const monthCell = document.createElement("td");
            monthCell.textContent = episode.broadcast_month;

            row.appendChild(idCell);
            row.appendChild(titleCell);
            row.appendChild(airDateCell);
            row.appendChild(monthCell);

            episodesTableBody.appendChild(row);
        });
    }

    // Function to handle filter form submission
    filterForm.addEventListener("submit", (e) => {
        e.preventDefault();

        const broadcastMonth = document.getElementById("broadcast-month").value;
        const subject = document.getElementById("subject").value;
        const color = document.getElementById("color").value;
        const matchAll = document.getElementById("match-all").checked;

        // Prepare filter parameters
        const filters = {};
        if (broadcastMonth) filters.broadcast_month = broadcastMonth;
        if (subject) filters.subject = subject;
        if (color) filters.color = color;
        filters.match_all = matchAll;

        fetchEpisodes(filters); // Fetch episodes based on filters
    });

    // Fetch and display episodes on initial load
    fetchEpisodes();
});