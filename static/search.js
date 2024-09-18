async function performSearch() {
    const searchTerm = document.getElementById('searchInput').value;
    const resultsContainer = document.getElementById('results');

    // Clear previous results
    resultsContainer.innerHTML = '';

    // Show loading message
    resultsContainer.innerHTML = '<div style="display: flex; justify-content: center; align-items: center; height: 100%;"><p>Searching...</p></div>';

    try {
        // Make a Fetch API call to your backend
        const response = await fetch(`/search?query=${encodeURIComponent(searchTerm)}`);

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.json();

        console.log('Raw data from backend:', data);  // Log the raw data

        // Parse the data
        const parsedData = data.map(item => {
            console.log('Processing item:', item);  // Log each item

            // Check if item is a string that contains a filename and JSON object
            if (typeof item === 'string') {
                const match = item.match(/(.+?)_([a-zA-Z]+)_(\d{4})/);
                if (match) {
                    const [fullMatch, folder, fileType, year] = match;
                    return {
                        name: `${folder}_${fileType}_${year}`,
                        folder: folder,
                        fileType: fileType,
                        year: year
                    };
                } else {
                    console.error('Unexpected string format:', item);
                    return { name: item, folder: 'Unknown' };
                }
            } else if (typeof item === 'object' && item !== null) {
                return item;  // If it's already an object, return it as is
            } else {
                console.error('Unexpected item type:', typeof item);
                return { name: String(item), folder: 'Unknown' };
            }
        });

        console.log('Parsed data:', parsedData);  // Log the parsed data

        resultsContainer.innerHTML = ''; // Clear loading message

        if (parsedData.length === 0) {
            resultsContainer.innerHTML = '<p>No results found.</p>';
            return;
        }
        // Group results by folder
        const groupedResults = parsedData.reduce((acc, item) => {
            if (!acc[item.folder]) {
                acc[item.folder] = [];
            }
            acc[item.folder].push(item);
            return acc;
        }, {});

        // Create a container for all columns
        const columnsContainer = document.createElement('div');
        columnsContainer.className = 'columns-container';
        columnsContainer.style.display = 'flex';
        columnsContainer.style.flexDirection = 'row';
        columnsContainer.style.justifyContent = 'space-between';
        resultsContainer.appendChild(columnsContainer);

        // Display grouped results in columns
        Object.entries(groupedResults).forEach(([folder, items]) => {
            const columnElement = document.createElement('div');
            columnElement.className = 'result-column';
            columnElement.style.flex = '1';
            columnElement.style.marginRight = '20px';
            
            const folderElement = document.createElement('div');
            folderElement.className = 'folder-group';
            folderElement.innerHTML = `
                <h3 class="folder-name">${folder}</h3>
                <div class="folder-items">
                </div>
            `;

            const folderItems = folderElement.querySelector('.folder-items');
            items.forEach(item => {
                const resultElement = document.createElement('div');
                resultElement.className = 'search-result';
                let contentHTML = `
                    <div class="result-content">
                        <div class="file-info">
                            <p class="file-name">${item.name}</p>
                            <div class="action-icons">`;

                if (item.webViewLink && item.name.toLowerCase().endsWith('.jpg')) {
                    contentHTML += `
                                <a href="${item.webViewLink}" target="_blank" title="View file" class="icon-button">
                                    <i class="fas fa-eye"></i>
                                </a>`;
                }

                if (item.webContentLink) {
                    contentHTML += `
                                <a href="${item.webContentLink}" download title="Download file" class="icon-button">
                                    <i class="fas fa-download"></i>
                                </a>`;
                }

                contentHTML += `
                            </div>
                        </div>
                    </div>`;

                if (item.thumbnailLink && item.name.toLowerCase().endsWith('.jpg')) {
                    contentHTML += `<img src="${item.thumbnailLink}" alt="${item.name}" class="thumbnail">`;
                }

                resultElement.innerHTML = contentHTML;
                folderItems.appendChild(resultElement);
            });

            columnElement.appendChild(folderElement);
            columnsContainer.appendChild(columnElement);
        });

    } catch (error) {
        console.error('Error:', error);
        resultsContainer.innerHTML = '<p>An error occurred while searching. Please try again.</p>';
    }
}
