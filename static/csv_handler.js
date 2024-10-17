let csvData = [];

// Function to load CSV file from the server
async function loadCSV() {
    const dataUrl = '/get_csv';
    try {
        const response = await fetch(dataUrl);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        csvData = await response.json();
        console.log('Data loaded successfully');
        console.log(csvData);
    } catch (error) {
        console.error('Error loading data:', error);
    }
}


// Function to get autocomplete suggestions
function getAutocompleteSuggestions(input) {
    if (input.length < 2) return [];
    
    const isNumeric = /^\d+$/.test(input);
    
    const filteredResults = csvData
        .filter(item => {
            if (isNumeric) {
                // If input is numeric, search in Index
                // Convert both to strings for comparison
                const itemIndex = String(item.Index);
                return itemIndex === input || itemIndex.startsWith(input);
            } else {
                // If input is text, search in DEN_BOT
                return item.DEN_BOT && item.DEN_BOT.toLowerCase().includes(input.toLowerCase());
            }
        });

    // Console log the exact match 
    const exactMatch = filteredResults.find(item => String(item.Index) === input);
    console.log('Exact match for input "' + input + '":', exactMatch);

    return filteredResults
        .map(item => ({Index: String(item.Index), DEN_BOT: item.DEN_BOT}))
        .sort((a, b) => parseInt(a.Index) - parseInt(b.Index)) // Sort by Index
        .slice(0, 10); // Limit to 10 suggestions
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
document.addEventListener('DOMContentLoaded', async () => {
    await loadCSV();  // Wait for CSV to load before setting up event listeners
    
    const searchInput = document.getElementById('searchInput');
    searchInput.addEventListener('input', () => {
        showAutocomplete(searchInput);
        console.log('User is typing:', searchInput.value);
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (e.target.id !== 'searchInput') {
            const dropdown = document.getElementById('autocompleteDropdown');
            if (dropdown) dropdown.remove();
        }
    });
});
