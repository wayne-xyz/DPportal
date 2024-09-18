require(["esri/config", "esri/Map", "esri/views/MapView"], function(esriConfig, Map, MapView) {

    esriConfig.apiKey = "YOUR_ACCESS_TOKEN";
  
    const map = new Map({
      basemap: "arcgis/topographic" // basemap styles service
    });
  
    const view = new MapView({
      map: map,
      center: [-118.805, 34.027], // Longitude, latitude
      zoom: 13, // Zoom level
      container: "map" // Div element
    });
  
});
  