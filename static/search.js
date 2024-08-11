async function performSearch() {
    const searchTerm = document.getElementById('searchInput').value;
    const resultsContainer = document.getElementById('results');
    
    // Clear previous results
    resultsContainer.innerHTML = '';
    
    // Show loading message
    resultsContainer.innerHTML = '<p>Searching...</p>';
    
    try {
        // Make a Fetch API call to your backend
        const response = await fetch(`/search?query=${encodeURIComponent(searchTerm)}`);
        
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        
        const data = await response.json();
        
        resultsContainer.innerHTML = ''; // Clear loading message
        
        if (data.length === 0) {
            resultsContainer.innerHTML = '<p>No results found.</p>';
            return;
        }
        
        // Display each search result
        data.forEach(item => {
            const resultElement = document.createElement('div');
            resultElement.className = 'search-result';
            resultElement.innerHTML = `
                <h3>${item.name}</h3>
                <p>Folder: ${item.folder}</p>
            `;
            resultsContainer.appendChild(resultElement);
        });
    } catch (error) {
        console.error('Error:', error);
        resultsContainer.innerHTML = '<p>An error occurred while searching. Please try again.</p>';
    }
}
