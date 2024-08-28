let csvData = [];

// Function to load CSV file and store in local storage
async function loadAndStoreCSV() {
    const csvUrl = '/get_csv';  // Updated to match the Flask route
    const storageKey = 'shapefileData';

    // Check if data is already in local storage
    if (!localStorage.getItem(storageKey)) {
        try {
            const response = await fetch(csvUrl);
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const csvText = await response.text();
            localStorage.setItem(storageKey, csvText);
            console.log('CSV data loaded and stored in local storage');
        } catch (error) {
            console.error('Error loading CSV file:', error);
        }
    } else {
        console.log('CSV data already exists in local storage');
    }
    
    // Parse CSV data
    const csvText = localStorage.getItem(storageKey);
    csvData = parseCSV(csvText);
}

// Function to parse CSV data
function parseCSV(csvText) {
    const lines = csvText.split('\n');
    const headers = lines[0].split(',');
    return lines.slice(1).map(line => {
        const values = line.split(',');
        return headers.reduce((obj, header, index) => {
            obj[header.trim()] = values[index];
            return obj;
        }, {});
    });
}

// Function to get autocomplete suggestions
function getAutocompleteSuggestions(input) {
    if (input.length < 2) return [];
    
    const isNumeric = /^\d+$/.test(input);
    
    return csvData
        .filter(item => {
            if (isNumeric) {
                // If input is numeric, search in Index
                return item.Index && item.Index.toLowerCase().startsWith(input.toLowerCase());
            } else {
                // If input is text, search in DEN_BOT
                return item.DEN_BOT && item.DEN_BOT.toLowerCase().includes(input.toLowerCase());
            }
        })
        .map(item => ({Index: item.Index, DEN_BOT: item.DEN_BOT}))
        .slice(0, 5); // Limit to 5 suggestions
}

// Function to create and show autocomplete dropdown
function showAutocomplete(input) {
    const suggestions = getAutocompleteSuggestions(input.value);
    
    // Remove existing dropdown if any
    const existingDropdown = document.getElementById('autocompleteDropdown');
    if (existingDropdown) existingDropdown.remove();
    
    if (suggestions.length === 0) return;
    
    const dropdown = document.createElement('ul');
    dropdown.id = 'autocompleteDropdown';
    dropdown.style.position = 'absolute';
    dropdown.style.zIndex = '1000';
    dropdown.style.backgroundColor = 'white';
    dropdown.style.border = '1px solid #ddd';
    dropdown.style.maxHeight = '200px';
    dropdown.style.overflowY = 'auto';
    dropdown.style.listStyleType = 'none';
    dropdown.style.padding = '0';
    dropdown.style.margin = '0';
    dropdown.style.width = input.offsetWidth + 'px';
    
    suggestions.forEach(suggestion => {
        const li = document.createElement('li');
        li.innerHTML = `<strong>${suggestion.Index}</strong>: ${suggestion.DEN_BOT}`;
        li.style.padding = '10px';
        li.style.cursor = 'pointer';
        li.addEventListener('click', () => {
            input.value = suggestion.Index;
            dropdown.remove();
        });
        li.addEventListener('mouseover', () => {
            li.style.backgroundColor = '#f0f0f0';
        });
        li.addEventListener('mouseout', () => {
            li.style.backgroundColor = 'white';
        });
        dropdown.appendChild(li);
    });
    
    input.parentNode.appendChild(dropdown);
    dropdown.style.top = (input.offsetTop + input.offsetHeight) + 'px';
    dropdown.style.left = input.offsetLeft + 'px';
}

// Load CSV data when the page loads
document.addEventListener('DOMContentLoaded', () => {
    loadAndStoreCSV();
    
    const searchInput = document.getElementById('searchInput');
    searchInput.addEventListener('input', () => {
        showAutocomplete(searchInput);
        console.log('User is typing:', searchInput.value);  // New line to print as user types
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (e.target.id !== 'searchInput') {
            const dropdown = document.getElementById('autocompleteDropdown');
            if (dropdown) dropdown.remove();
        }
    });
});
