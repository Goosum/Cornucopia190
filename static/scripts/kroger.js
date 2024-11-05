function callDatabase(searchSettings) {
  $.ajax(searchSettings).done(function (response) {
    return response
    });
}

function getAuthToken() {

}

function getSettingsbyTerm(searchTerm, limit, authToken) {
  let settings = {
    "async": true,
    "crossDomain": true,
    "url": "https://api.kroger.com/v1/products?filter.term=${searchTerm}&filter.limit=${limit}",
    "method": "GET",
    "headers": {
      "Accept": "application/json",
      "Authorization": "Bearer ${authToken}"
    }
  }
  return settings;
}

function getProductsbyTerm(searchTerm, limit) {
  let searchSettings = getSettingsbyTerm(searchTerm, limit, getAuthToken());
  return callDatabase(searchSettings);
}
