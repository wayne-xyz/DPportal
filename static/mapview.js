// Fetch the API key before initializing the map
fetch('/get_esri_api_key')
  .then(response => response.json())
  .then(data => {
    // Once we have the API key, initialize the map
    require([
      "esri/config", 
      "esri/Map", 
      "esri/views/MapView",
      "esri/layers/FeatureLayer"
    ], function(esriConfig, Map, MapView, FeatureLayer) {

      esriConfig.apiKey = data.api_key;
    
      const map = new Map({
        basemap: "arcgis/imagery"
      });
    
      const view = new MapView({
        map: map,
        center: [-75.015, -9.19],
        zoom: 5,
        container: "map"
      });

      // Create the feature layer
      const peruLayer = new FeatureLayer({
        url: "https://services5.arcgis.com/278L6SNPC4FKp6eI/arcgis/rest/services/peru_dp/FeatureServer"
      });

      // Add the layer to the map
      map.add(peruLayer);

      // Optional: You can hide the layer initially and show it when needed
      peruLayer.visible = false;

      // Function to show the layer
      window.showPeruLayer = function() {
        peruLayer.visible = true;
      }

      // Function to hide the layer
      window.hidePeruLayer = function() {
        peruLayer.visible = false;
      }

      window.zoomToFeature = function(indexValue) {
        // Query the feature layer for the feature with the given Index_1 value
        const query = peruLayer.createQuery();
        query.where = `Index_1 = ${indexValue}`;
        query.outFields = ["*"];
        query.returnGeometry = true;

        peruLayer.queryFeatures(query).then(function(results) {
          if (results.features.length > 0) {
            const feature = results.features[0];

            // Import the Graphic module
            require(["esri/Graphic"], function(Graphic) {
              // add label to the feature with the value of Index_1
              const labelGraphic = new Graphic({
                geometry: feature.geometry,
                symbol: {
                  type: "text",
                  color: "black",
                  haloColor: "white",
                  haloSize: "2px",
                  text: `${feature.attributes.Index_1}`,
                  font: {
                    size: 12,
                    weight: "bold"
                  }
                }
              });

              // add the label to the view
              view.graphics.add(labelGraphic);
            });



            // zoom to the feature
            view.goTo({
              target: feature.geometry,
              zoom: 20
            });
          } else {
            console.log("Feature not found");
          }
        }).catch(function(error) {
          console.error("Error querying feature:", error);
        });
      }



    });
  })
  .catch(error => {
    console.error('Error fetching API key:', error);
    // Handle the error appropriately, e.g., show an error message to the user
  });
