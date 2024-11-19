// Loading state management
function showLoading() {
    document.getElementById('loading').style.display = 'flex';
    document.getElementById('statistics-table').style.display = 'none';
    document.getElementById('error-message').style.display = 'none';
    document.getElementById('statistics-title').style.display = 'none';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

function showError(message) {
    const errorDiv = document.getElementById('error-message');
    errorDiv.innerHTML = `
        ${message}
        <br>
        <button onclick="fetchStatistics()" class="retry-button">Try Again</button>
    `;
    errorDiv.style.display = 'block';
}

// Add this function to format the date
function formatDateTime(isoString) {
    const date = new Date(isoString);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// Display data in table
function displayStatistics(response) {
    const table = document.getElementById('statistics-table');
    const title = document.getElementById('statistics-title');
    const tbody = table.querySelector('tbody');
    tbody.innerHTML = ''; // Clear existing content
    
    // Add last updated time
    const lastUpdatedDiv = document.getElementById('last-updated');
    if (response.lastUpdated) {
        lastUpdatedDiv.textContent = `Last Updated: ${formatDateTime(response.lastUpdated)}`;
        lastUpdatedDiv.style.display = 'block';
    }
    
    // Add each row to table
    response.data.forEach(row => {
        const tr = document.createElement('tr');
        
        // Format numbers with thousands separator
        const nicfiTif = parseInt(row['NICFI TIF']).toLocaleString();
        const nicfiJpg = parseInt(row['NICFI JPG']).toLocaleString();
        const sentinelTif = parseInt(row['Sentinel-2 TIF']).toLocaleString();
        const sentinelJpg = parseInt(row['Sentinel-2 JPG']).toLocaleString();
        
        tr.innerHTML = `
            <td>${row.Month}</td>
            <td class="number-cell">${nicfiTif}</td>
            <td class="number-cell">${nicfiJpg}</td>
            <td class="number-cell">${sentinelTif}</td>
            <td class="number-cell">${sentinelJpg}</td>
        `;
        tbody.appendChild(tr);
    });
    
    // Show table with fade-in effect
    table.style.display = 'table';
    title.style.display = 'block';

    title.style.opacity = '0';
    table.style.opacity = '0';
    setTimeout(() => {
        table.style.transition = 'opacity 0.3s ease-in';
        table.style.opacity = '1';
        title.style.transition = 'opacity 0.3s ease-in';
        title.style.opacity = '1';
    }, 100);
}

// Main function to fetch and display data
async function fetchStatistics() {
    showLoading();
    
    try {
        const response = await fetch('/get_statistics_csv');
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to fetch statistics');
        }
        
        const data = await response.json();
        hideLoading();
        displayStatistics(data);
        
    } catch (error) {
        console.error('Error:', error);
        hideLoading();
        showError('Failed to load statistics. Please try again later.');
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', fetchStatistics);