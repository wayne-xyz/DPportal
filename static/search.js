// Function to load the JSON mapping file
function loadMapping(callback) {
    const xhr = new XMLHttpRequest();
    xhr.open('GET', '/static/strMapping.json', true); // true makes the request asynchronous
    xhr.onload = function() {
        if (xhr.status === 200) {
            const strMapping = JSON.parse(xhr.responseText);
            console.log('Mapping loaded:', strMapping);
            callback(strMapping);
        } else {
            console.error('Error loading mapping:', xhr.statusText);
            callback({});
        }
    };
    xhr.onerror = function() {
        console.error('Network error while loading mapping.');
        callback({});
    };
    xhr.send();
}

// Function to add hover text
function addHoverText(element, hoverText) {
    const hoverElement = document.createElement('span');
    hoverElement.className = 'hover-text';
    hoverElement.innerHTML = hoverText; // Use innerHTML to support HTML content
    hoverElement.style.position = 'absolute';
    hoverElement.style.backgroundColor = '#333';
    hoverElement.style.color = '#fff';
    hoverElement.style.padding = '5px';
    hoverElement.style.borderRadius = '5px';
    hoverElement.style.whiteSpace = 'normal'; // Allow text to wrap
    hoverElement.style.visibility = 'hidden';
    hoverElement.style.opacity = '0';
    hoverElement.style.transition = 'opacity 0.3s';
    hoverElement.style.maxWidth = '400px'; // Optional: limit the width of the hover text

    element.style.position = 'relative';
    element.appendChild(hoverElement);

    element.addEventListener('mouseenter', () => {
        hoverElement.style.visibility = 'visible';
        hoverElement.style.opacity = '1';
    });

    element.addEventListener('mouseleave', () => {
        hoverElement.style.visibility = 'hidden';
        hoverElement.style.opacity = '0';
    });
}

// Define performSearch as a global function
window.performSearch = function() {
    loadMapping(async function(strMapping) {
        const searchTerm = document.getElementById('searchInput').value;
        const resultsContainer = document.getElementById('results');
        const mapContainer = document.getElementById('map'); // control the map container show or hide

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
                mapContainer.classList.add('hidden'); // Hide the map
                window.hidePeruLayer();
                return;
            }

            //  contro the mapview show and perform the zoom to the feature

            // Show the map when results are found
            mapContainer.classList.remove('hidden');
            
            window.showPeruLayer();

            // convert the search item to the integer value and zoom to the feature
            const indexValue = parseInt(searchTerm);
            window.zoomToFeature(indexValue);
             

            

            // Group results by folder
            const groupedResults = parsedData.reduce((acc, item) => {
                if (!acc[item.folder]) {
                    acc[item.folder] = [];
                }
                acc[item.folder].push(item);
                return acc;
            }, {});

            // Create a container for the toggle button and columns
            const resultsWrapper = document.createElement('div');
            resultsWrapper.className = 'results-wrapper';
            resultsWrapper.style.display = 'flex';
            resultsWrapper.style.flexDirection = 'column';
            resultsWrapper.style.position = 'relative';  // Add this line
            resultsContainer.appendChild(resultsWrapper);

            // Create a button to toggle expanded view
            const toggleButton = document.createElement('button');
            toggleButton.textContent = 'Show TIFF files';
            toggleButton.style.position = 'absolute';
            toggleButton.style.top = '0';
            toggleButton.style.right = '0';
            toggleButton.style.zIndex = '1';
            resultsWrapper.appendChild(toggleButton);

            // Create a scrollable container for columns
            const scrollContainer = document.createElement('div');
            scrollContainer.className = 'scroll-container';
            scrollContainer.style.overflowX = 'hidden';
            scrollContainer.style.width = '100%';
            scrollContainer.style.marginTop = '40px';  // Add space for the button
            resultsWrapper.appendChild(scrollContainer);

            // Create a container for all columns
            const columnsContainer = document.createElement('div');
            columnsContainer.className = 'columns-container';
            columnsContainer.style.display = 'flex';
            columnsContainer.style.flexDirection = 'row';
            columnsContainer.style.justifyContent = 'flex-start';
            columnsContainer.style.flexWrap = 'nowrap';
            columnsContainer.style.minWidth = '100%';
            scrollContainer.appendChild(columnsContainer);

            let isExpanded = false;

            // Display grouped results in columns
            Object.entries(groupedResults).forEach(([folder, items], index) => {
                const columnElement = document.createElement('div');
                columnElement.className = 'result-column';
                columnElement.style.flex = '0 0 calc(33.33% - 20px)';
                columnElement.style.marginRight = '20px';
                columnElement.style.marginBottom = '20px';
                
                if (index >= Object.keys(groupedResults).length - 2) {
                    columnElement.style.display = 'none';
                    columnElement.classList.add('collapsed-column');
                }

                // Use the mapping to get the display name and description
                const displayName = strMapping[folder] || folder;
                const description = strMapping[`${folder} description`] || '';

                const folderElement = document.createElement('div');
                folderElement.className = 'folder-group';
                
                folderElement.innerHTML = `
                    <h3 class="folder-name">${displayName}</h3>
                    <div class="folder-items">
                    </div>
                `;

                // Add hover text to the folder name
                const folderNameElement = folderElement.querySelector('.folder-name');
                addHoverText(folderNameElement, description);

                items.forEach((item, index) => {
                    const resultElement = document.createElement('div');
                    resultElement.className = 'search-result';
                    let contentHTML = `
                        <div class="result-content">
                            <div class="file-info">
                                <p class="file-name small-text">${item.name}</p>
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
                        const match = item.name.match(/(\d+)-(\d{4})(\d{2})(\d{2})/);
                        let formattedText = '';
                        if (match) {
                            const [, index, year, month, day] = match;
                            const date = new Date(year, month - 1, day);
                            const formattedDate = date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
                            formattedText = `${index} - ${formattedDate}`;
                        }

                        contentHTML += `
                            <div class="thumbnail-container" style="display: flex; align-items: center;">
                                <img src="${item.thumbnailLink}" alt="${item.name}" class="thumbnail" style="margin-right: 10px;">
                                <span class="file-info-text">${formattedText}</span>
                            </div>`;
                    }

                    resultElement.innerHTML = contentHTML;
                    folderElement.querySelector('.folder-items').appendChild(resultElement);
                });

                columnElement.appendChild(folderElement);
                columnsContainer.appendChild(columnElement);
            });

            // Add click event listener to toggle button
            toggleButton.addEventListener('click', () => {
                isExpanded = !isExpanded;
                const collapsedColumns = columnsContainer.querySelectorAll('.collapsed-column');
                collapsedColumns.forEach((column) => {
                    column.style.display = isExpanded ? 'block' : 'none';
                });
                scrollContainer.style.overflowX = isExpanded ? 'auto' : 'hidden';
                toggleButton.textContent = isExpanded ? 'Show JPG files' : 'Show TIFF files';

                // Scroll to the right when expanded
                if (isExpanded) {
                    scrollContainer.scrollLeft = scrollContainer.scrollWidth;
                }
            });

        } catch (error) {
            console.error('Error:', error);
            resultsContainer.innerHTML = '<p>An error occurred while searching. Please try again.</p>';
            mapContainer.classList.add('hidden'); // Hide the map on error
        }
    });
};
