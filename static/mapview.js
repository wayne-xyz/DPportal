// Fetch the API key before initializing the map
fetch('/get_esri_api_key')
  .then(response => response.json())
  .then(data => {
    // Once we have the API key, initialize the map
    require(["esri/config", "esri/Map", "esri/views/MapView"], function(esriConfig, Map, MapView) {

      esriConfig.apiKey = data.api_key;
    
      const map = new Map({
        basemap: "arcgis/imagery" // basemap styles service
      });
    
      const view = new MapView({
        map: map,
        center: [-118.805, 34.027], // Longitude, latitude
        zoom: 13, // Zoom level
        container: "map" // Div element
      });
    
    });
  })
  .catch(error => {
    console.error('Error fetching API key:', error);
    // Handle the error appropriately, e.g., show an error message to the user
  });
