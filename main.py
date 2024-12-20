from flask import Flask 
from flask import render_template 
from flask import request
from flask import redirect
from flask import session
from flask import Flask, render_template, redirect, url_for, session, request, jsonify, flash
import mariadb
import sys
import bcrypt

import kroger
  
app = Flask(__name__) 
app.secret_key = 'supersecretkey'



@app.route('/')
@app.route('/home')
def home():
    token = kroger.get_auth_token()
    all_products = kroger.get_hot_products(token)

    # Split products into rows of 6 each
    rows = [all_products[i] for i in range(len(all_products))]
    print(rows)
    
    username = session.get("user", "Guest")
    return render_template('home.html', products=rows, username=username)
 
@app.route('/search')
def search():
    token = kroger.get_auth_token()
    products = kroger.search_product(request.args.get('term') ,token)
    username = "Guest"
    if session.get("user"):
        username = session.get("user")
    return render_template('search.html', products=products, username=username)    


@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_id = str(request.json['product_id'])
    print(product_id)
    cart = session.get('cart', {})
    cart[product_id] = cart.get(product_id, 0) + 1
    session['cart'] = cart
    session['cart_total'] = sum(cart.values())
    return jsonify({'total_items': session['cart_total']})

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if session.get("user"):
        username = session.get("user")
        return render_template('profile.html', username = username)
    else:
        return redirect("login")

@app.route("/remove_account", methods = ['GET', 'POST'])
def remove_account():
    if request.method == 'GET':
        return render_template('login.html', header="Delete Account", redirect="remove_account", otherurl="register", otherpage="Login")
    elif  request.method == 'POST':
        data = request.form
        
        #connect to database
        conn = dbconnect()
        cur = conn.cursor()
        
        #retrieve username and pw from user
        username = data["user"]
        pw = data["pass"]

        #check username against database
        query = f"SELECT password FROM accounts.accounts WHERE username='{username}'"
        cur.execute(query)
        
        #fetch from database
        row = cur.fetchone()
        
        #check pw against username
        if row:
            encoded = bytes(data["pass"], 'utf-8')
            hash = bytes(row[0], 'utf-8')
            if bcrypt.checkpw(encoded, hash):
                #if correct, present confirmation button
                query = f"DELETE FROM accounts WHERE username='{username}'"
                cur.execute(query)
                conn.commit()

                session.clear()
                return redirect(url_for('home'))
                
            else: #case: wrong pw
                return "wrong credentials"
        else: #case: username not in database
            return "user does not exist"

@app.route('/cart')
def cart():
    username = session.get('user', 'Guest') 
    cart = session.get('cart', {})
    token = kroger.get_auth_token()
    
    cart_items = []
    
    for item in cart:
        newitem = {}
        x = kroger.get_product(item, token)
        newitem["name"] = x["name"]
        newitem["price"] = x["price"]
        newitem["price_formatted"] = x["price_formatted"]
        newitem["image"] = x["image"]
        newitem["quantity"] = cart[item]
        cart_items.append(newitem)
        
    print(cart_items)

    subtotal = sum(item["price"] * item["quantity"] for item in cart_items)
    subtotal_str = '${:,.2f}'.format(subtotal)
    tax = subtotal * 0.0863
    tax_str = '${:,.2f}'.format(tax)
    total = subtotal + tax
    total_str = '${:,.2f}'.format(total)
    

    return render_template('cart.html', cart=cart_items, subtotal=subtotal_str, tax=tax_str, total=total_str, username=username)

@app.route('/apply_coupon', methods=['POST'])
def apply_coupon():
    data = request.get_json()
    coupon = data.get('coupon', '').strip()

    valid_coupons = {
        "SAVE10": 10,  # $10 discount
        "SAVE20": 20   # $20 discount
    }

    if coupon not in valid_coupons:
        return jsonify({'error': 'Invalid coupon code'}), 400

    discount = valid_coupons[coupon]

    # Retrieve cart and product details
    cart = session.get('cart', {})
    if not isinstance(cart, dict):
        return jsonify({'error': 'Cart is not in a valid format'}), 500

    token = kroger.get_auth_token()
    products = kroger.get_hot_products(token)

    # Combine cart with product details
    cart_items = [{**p, "quantity": cart[str(p["id"])]} for p in products if str(p["id"]) in cart]

    try:
        subtotal = sum(item["price"] * item["quantity"] for item in cart_items)
        tax = subtotal * 0.0863
        total = subtotal - discount + tax

        if total < 0:
            total = 0

        return jsonify({'discount': discount, 'total': total})
    except KeyError as e:
        return jsonify({'error': f'Missing key in cart item: {e}'}), 500
    except Exception as e:
        return jsonify({'error': f'An error occurred: {e}'}), 500
    
@app.route('/clear_cart')
def clear_cart():
    session.pop('cart', None)
    session['cart_total'] = 0
    session.pop('discount', None)  
    return redirect(url_for('home'))

@app.route('/update_quantity/<product_id>', methods=['POST'])
def update_quantity(product_id):
    data = request.get_json()
    new_quantity = int(data.get('quantity', 1))
    cart = session.get('cart', {})

    if product_id in cart:
        if new_quantity > 0:
            cart[product_id] = new_quantity
        else:
            cart.pop(product_id)

    session['cart'] = cart

    try:
        token = kroger.get_auth_token()
        products = kroger.get_hot_products(token)
        cart_items = [
            {**p, "quantity": cart[str(p["id"])]}
            for p in products if str(p["id"]) in cart
        ]
        subtotal = sum(item["price"] * item["quantity"] for item in cart_items)
        tax = subtotal * 0.0863
        total = subtotal + tax
        session['cart_total'] = sum(cart.values())

        # Calculate prices for individual items
        item_prices = {str(p["id"]): p["price"] * cart[str(p["id"])] for p in products if str(p["id"]) in cart}

        return jsonify({'subtotal': subtotal, 'tax': tax, 'total': total, 'itemPrices': item_prices})
    except Exception as e:
        app.logger.error(f"Error updating quantity: {e}")
        return jsonify({'error': 'An error occurred'}), 500

@app.route('/checkout')
def checkout():
    username = session.get('user', 'Guest')
    cart = session.get('cart', {})
    token = kroger.get_auth_token()

    # Retrieve cart items with product details
    cart_items = []
    
    for item in cart:
        newitem = {}
        x = kroger.get_product(item, token)
        newitem["name"] = x["name"]
        newitem["price"] = x["price"]
        newitem["price_formatted"] = x["price_formatted"]
        newitem["image"] = x["image"]
        newitem["quantity"] = cart[item]
        cart_items.append(newitem)

    # Calculate subtotal, tax, and total
    subtotal = sum(item["price"] * item["quantity"] for item in cart_items)
    tax = subtotal * 0.0863
    discount = session.get('discount', 0)  # Get the discount from the session
    total = subtotal - discount + tax

    # Debug: Print values
    print(f"Cart items: {cart_items}")
    print(f"Subtotal: {subtotal}, Discount: {discount}, Tax: {tax}, Total: {total}, Coupon: {session.get('coupon', None)}")

    return render_template(
        'checkout.html',
        cart=cart_items,
        subtotal=subtotal,
        tax=tax,
        discount=discount,
        total=total,
        coupon=session.get('coupon', None),  # Get the applied coupon
        username=username
    )
    
@app.route('/process_checkout', methods=['POST'])
def process_checkout():
    name = request.form.get('name')
    address = request.form.get('address')
    payment = request.form.get('payment')

    session.pop('cart', None)
    session['cart_total'] = 0

    flash(f"Thank you, {name}! Your order has been placed successfully.", "success")
    return redirect(url_for('home'))

@app.route("/login", methods = ['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html', header="Log In", redirect="login", otherurl="register", otherpage="Register an Account")
    elif  request.method == 'POST':
        data = request.form
        conn = dbconnect()
        cur = conn.cursor()
        
        username = data["user"]
        
        query = f"SELECT password FROM accounts.accounts WHERE username='{username}'"
        
        cur.execute(query)
        
        row = cur.fetchone()
        
        if row:
            encoded = bytes(data["pass"], 'utf-8')
            hash = bytes(row[0], 'utf-8')
            if bcrypt.checkpw(encoded, hash):
                session["user"] = username
                return redirect("home")
            else:
                return "wrong credentials"
        else:
            return "user does not exist"

@app.route('/logout', methods = ['POST'])
def logout():
    # clear the session data
    session.clear()

    # redirect to the login page
    return redirect("home")

@app.route("/register", methods = ['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('login.html', header="Sign Up", redirect="register", otherurl="login", otherpage="Log in (Existing account)")
    elif  request.method == 'POST':
        data = request.form
        
        conn = dbconnect()
        cur = conn.cursor()
        
        username = data["user"]

        pw = data["pass"]

        bytes = pw.encode('utf-8') 
        
        salt = bcrypt.gensalt()
        salttxt = salt.decode("utf-8")
        
        # hashing the password 
        hashed = bcrypt.hashpw(bytes, salt).decode("utf-8")
        
        query = f"INSERT INTO accounts VALUES('{username}','{hashed}', '{salttxt}')"
        
        try:
            cur.execute(query)
        except:
            return "already exists"
        rowsupdated = cur.rowcount
        
        conn.commit()
        
        if(rowsupdated):
            return "ok"
        else:
            return "failure"


def dbconnect():
    try:
        conn = mariadb.connect(
            user="root",
            password="wgKv9xRzZ8ycGaJ2hBMYE7",
            host="192.168.1.164",
            port=3306,
            database="accounts"
        )
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    return conn

if __name__ == "__main__": 
    app.run(debug=True)