
import requests

def get_basic_auth_token():
    return "Y29ybnVjb3BpYTItMjQzMjYxMjQzMDM0MjQ0ZTQ2NmI0MTM2MzY2OTRiNTUyZTU5NmEzMDMyMzA2MjQ3NTU1OTZiNmM3NTUwNTY2Yjc2NjgyZTU0MzA2NTYyNjE0ZjY4NjU0NDRlNjMzNDY3NGY0NDUzNDQ3NDM2NzEzNjRkNzQ0YjZkMTMzNzM0MzU5NTUwMjk5MTcyOTprOUE2ZVo2Y0dhemp6RkhLNkNjNnNNSU4wbHJWMzdjMHZIb3l5M0Q4"

def get_auth_token():
    basic_token = "Basic " + get_basic_auth_token()
    auth_url = "https://api.kroger.com/v1/connect/oauth2/token"
    headers = {"Authorization": basic_token, "Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "client_credentials", "scope": "product.compact"}
    x = requests.post(auth_url, data = data, headers = headers)
    return x.json()["access_token"]

def get_hot_products(auth_token):
    filter = {"filter.term": "Kroger", "filter.limit": "5"}
    return get_products(filter, auth_token)
    
def search_product(term, auth_token):
    filter = {"filter.term": term, "filter.limit": "5"}
    return get_products(filter, auth_token)

def get_products(filter, auth_token):
    products_url = "https://api.kroger.com/v1/products"
    bearer = "Bearer " + auth_token
    headers = {"Authorization": bearer}
    x = requests.get(products_url, headers = headers, params = filter)
    return filter_json(x.json())

def filter_json(json):
    products = []
    id = 0
    for prod in json["data"]:
        newprod = {}
        newprod["name"] = prod["description"]
        newprod["image"] = prod["images"][1]["sizes"][1]["url"]
        newprod["id"] = id
        newprod["price"] = 5

        id = id + 1
        products.append(newprod)
    return products
