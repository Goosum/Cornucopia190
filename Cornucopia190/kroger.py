
import requests
import random

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
    #initialize displayed products list
    products = []
    filterlist = ["Kroger","Milk","Chicken","Cheese","Bread","Beef","Soda","Fruit","Vegetable"]
    #select 5 random products from preselected filter lists to be displayed
    for x in range(5):
        #randomly select filter term
        num = random.randint(1, len(filterlist))
        filterterm = filterlist[num-1]
        #set filter term and pass on to get product information
        filter = {"filter.term": filterterm, "filter.limit": "5", "filter.locationId": "01100002"}
        products = get_hot_products_intermediary(filter, auth_token, products)
    return products
    
def search_product(term, auth_token):  #todo change location later
    filter = {"filter.term": term, "filter.limit": "6", "filter.locationId": "01100002"}
    return get_products(filter, auth_token)

def get_product(id, auth_token):
    products_url = "https://api.kroger.com/v1/products/" + id
    bearer = "Bearer " + auth_token
    headers = {"Authorization": bearer}
    filter = {"filter.locationId": "01100002"}
    x = requests.get(products_url, headers = headers, params = filter)
    return filter_json(x.json())

def get_products(filter, auth_token):
    products_url = "https://api.kroger.com/v1/products/"
    bearer = "Bearer " + auth_token
    headers = {"Authorization": bearer}
    x = requests.get(products_url, headers = headers, params = filter) 
    products = []
    for prod in x.json()["data"]:
        newprod = filter_json(prod)
        products.append(newprod)
    return products

def get_hot_products_intermediary(filter, auth_token, products):
    #api request
    products_url = "https://api.kroger.com/v1/products/"
    bearer = "Bearer " + auth_token
    headers = {"Authorization": bearer}
    x = requests.get(products_url, headers = headers, params = filter) 
    #initialize list for trimmed json files
    newprods = []
    num2 = random.randint(1, 5)
    for prod in x.json()["data"]:
        newprod = filter_json(prod)
        newprods.append(newprod)
    #randomly select from filtered json files one product to be displayed
    products.append(newprods[num2-1])
    return products

def filter_json(prod):
    newprod = {}
    newprod["name"] = prod["description"]
    try:
        newprod["image"] = prod["images"][0]["sizes"][0]["url"]
    except:
        newprod["image"] = "https://platform.foodi-menus.com/static/media/placeholder_food.91ea4630.png"
    newprod["id"] = prod["upc"]
    price_obj = prod["items"][0]["price"]
    newprod["price"] = price_obj["regular"] - price_obj["promo"]
    newprod["price_formatted"] = '${:,.2f}'.format(newprod["price"])
    return newprod