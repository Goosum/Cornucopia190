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
def home():
    token = kroger.get_auth_token()
    products = kroger.get_hot_products(token)
    username = session.get("user", "Guest")
    return render_template('home.html', products=products, username=username)
<<<<<<< Updated upstream
    
    
@app.route('/search')
def search():
    token = kroger.get_auth_token()
    products = kroger.search_product(request.args.get('term') ,token)
    splitproducts = [products[x:x+3] for x in range(0, len(products),3)]
    username = "Guest"
    if session.get("user"):
        username = session.get("user")
    return render_template('search.html', splitproducts=splitproducts, username=username)    
=======

>>>>>>> Stashed changes

@app.route('/cart')
def cart():
    username = session.get('user', 'Guest') 
    cart = session.get('cart', {})
    token = kroger.get_auth_token()
    products = kroger.get_hot_products(token)

    cart_items = [{**p, "quantity": cart[str(p["id"])]} for p in products if str(p["id"]) in cart]
    subtotal = sum(item["price"] * item["quantity"] for item in cart_items)
    tax = subtotal * 0.0863
    total = subtotal + tax

    return render_template('cart.html', cart=cart_items, subtotal=subtotal, tax=tax, total=total, username=username)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_id = str(request.json['product_id'])
    cart = session.get('cart', {})
    cart[product_id] = cart.get(product_id, 0) + 1
    session['cart'] = cart
    session['cart_total'] = sum(cart.values())
    return jsonify({'total_items': session['cart_total']})

@app.route('/apply_coupon', methods=['POST'])
def apply_coupon():
    coupon = request.form.get('coupon')
    if coupon == "SAVE10":
        session['discount'] = 0.10  # 10% discount
        flash("Coupon applied successfully! You saved 10%.", "success")
    elif coupon == "SAVE20":
        session['discount'] = 0.20  # 20% discount
        flash("Coupon applied successfully! You saved 20%.", "success")
    else:
        session['discount'] = 0  # No discount
        flash("Invalid coupon code.", "error")
    return redirect(url_for('cart'))  # Redirect back to the cart page

@app.route('/clear_cart')
def clear_cart():
    session.pop('cart', None)
    session['cart_total'] = 0
    return redirect(url_for('cart'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember')

        if validate_login(username, password):  # Validate user credentials
            session["user"] = username
            return redirect(url_for('home'))
        else:
            cart.pop(product_id)  

    session['cart'] = cart

    token = kroger.get_auth_token()
    products = kroger.get_hot_products(token)
    cart_items = [{**p, "quantity": cart[str(p["id"])]} for p in products if str(p["id"]) in cart]
    subtotal = sum(item["price"] * item["quantity"] for item in cart_items)
    tax = subtotal * 0.0863
    total = subtotal + tax

    session['cart_total'] = sum(cart.values())

    return jsonify({'subtotal': subtotal, 'tax': tax, 'total': total})

@app.route('/checkout')
def checkout():
    username = session.get('user', 'Guest')  
    cart = session.get('cart', {})
    token = kroger.get_auth_token()
    products = kroger.get_hot_products(token)

    cart_items = [{**p, "quantity": cart[str(p["id"])]} for p in products if str(p["id"]) in cart]
    subtotal = sum(item["price"] * item["quantity"] for item in cart_items)
    tax = subtotal * 0.0863
    total = subtotal + tax

    return render_template('checkout.html', cart=cart_items, subtotal=subtotal, tax=tax, total=total, username=username)

@app.route('/process_checkout', methods=['POST'])
def process_checkout():
    name = request.form.get('name')
    address = request.form.get('address')
    payment = request.form.get('payment')

    session.pop('cart', None)
    session['cart_total'] = 0

    flash(f"Thank you, {name}! Your order has been placed successfully.", "success")
    return redirect(url_for('home'))

@app.route("/login.html", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html', header="Log In", redirect="login", otherurl="register", otherpage="Register an Account")
    elif request.method == 'POST':
        data = request.form
        
        conn = dbconnect()
        cur = conn.cursor()

        username = data["user"]
        query = "SELECT password FROM accounts.accounts WHERE username=%s"
        cur.execute(query, (username,))

        row = cur.fetchone()

        if row:
            encoded = data["pass"].encode('utf-8')
            hashed = row[0].encode('utf-8')
            if bcrypt.checkpw(encoded, hashed):
                session["user"] = username
                return redirect(url_for('home'))
            else:
                flash("Wrong credentials.", "error")
                return redirect(url_for('login'))
        else:
            flash("User does not exist.", "error")
            return redirect(url_for('login'))

<<<<<<< Updated upstream
@app.route("/register.html", methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('login.html', header="Sign Up", redirect="register.html", otherurl="login.html", otherpage="Log in (Existing account)")
    elif  request.method == 'POST':
        data = request.form
        
        conn = dbconnect()
        cur = conn.cursor()
        
        username = data["user"]

        pw = data["pass"]

        bytes = pw.encode('utf-8') 
        
        salt = bcrypt.gensalt()
        salttxt = salt.decode("utf-8")
        
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

=======
@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('login.html', header="Sign Up", redirect="register", otherurl="login", otherpage="Log in (Existing account)")
    elif request.method == 'POST':
        data = request.form
        conn = dbconnect()
        cur = conn.cursor()

        username = data["user"]
        pw = data["pass"]

        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(pw.encode('utf-8'), salt)

        try:
            query = "INSERT INTO accounts (username, password, salt) VALUES (%s, %s, %s)"
            cur.execute(query, (username, hashed.decode('utf-8'), salt.decode('utf-8')))
            conn.commit()
            flash("Account created successfully.", "success")
            return redirect(url_for('login'))
        except mariadb.Error:
            flash("Account already exists.", "error")
            return redirect(url_for('register'))

def validate_login(username, password):
    """Validate user login credentials."""
    conn = dbconnect()
    cur = conn.cursor()
    query = "SELECT password FROM accounts.accounts WHERE username=%s"
    cur.execute(query, (username,))
    row = cur.fetchone()
    if row:
        return bcrypt.checkpw(password.encode('utf-8'), row[0].encode('utf-8'))
    return False

>>>>>>> Stashed changes
def dbconnect():
    try:
        conn = mariadb.connect(
            user="root",
            password="admin",
            host="192.168.1.164",
            port=3306,
            database="accounts"
        )
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    return conn

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').lower()  # Get search query
    category = request.args.get('category', 'all').lower()  # Get category filter

    token = kroger.get_auth_token()
    products = kroger.get_hot_products(token)

    # Filter products based on the query and category
    filtered_products = [
        product for product in products 
        if query in product['name'].lower() and (category == 'all' or category in product['category'].lower())
    ]

    # Handle no results
    if not filtered_products:
        flash("No products found for your search.", "info")
    
    return render_template('home.html', products=filtered_products, username=session.get("user", "Guest"))



    if __name__ == "__main__":
        app.run(debug=True, host="127.0.0.1", port=5000)

