function performSearch() {
    const searchTerm = document.getElementById('searchInput').value;
    const resultsContainer = document.getElementById('results');
    
    // Clear previous results
    resultsContainer.innerHTML = '';
    
    // Show loading message
    resultsContainer.innerHTML = '<p>Searching...</p>';
    
    // Make an AJAX call to your backend
    fetch(`/search?query=${encodeURIComponent(searchTerm)}`)
        .then(response => response.json())
        .then(data => {
            resultsContainer.innerHTML = ''; // Clear loading message
            
            if (data.length === 0) {
                resultsContainer.innerHTML = '<p>No results found.</p>';
                return;
            }
            
            // Display each image result
            data.forEach(item => {
                const imageElement = document.createElement('div');
                imageElement.className = 'image-result';
                imageElement.innerHTML = `
                    <img src="${item.thumbnailLink}" alt="${item.name}">
                    <p>${item.name}</p>
                `;
                resultsContainer.appendChild(imageElement);
            });
        })
        .catch(error => {
            console.error('Error:', error);
            resultsContainer.innerHTML = '<p>An error occurred while searching. Please try again.</p>';
        });
}