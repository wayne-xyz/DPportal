// Loading state management
function showLoading() {
    document.getElementById('loading').style.display = 'flex';
    document.getElementById('statistics-table').style.display = 'none';
    document.getElementById('error-message').style.display = 'none';
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

// Display data in table
function displayStatistics(data) {
    const table = document.getElementById('statistics-table');
    const tbody = table.querySelector('tbody');
    tbody.innerHTML = ''; // Clear existing content
    
    // Add each row to table
    data.forEach(row => {
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
    table.style.opacity = '0';
    setTimeout(() => {
        table.style.transition = 'opacity 0.3s ease-in';
        table.style.opacity = '1';
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