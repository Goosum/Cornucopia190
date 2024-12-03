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
    username = "Guest"
    if session.get("user"):
        username = session.get("user")
    return render_template('home.html', products=products, username=username)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_id = str(request.json['product_id'])
    print(product_id)
    cart = session.get('cart', {})
    cart[product_id] = cart.get(product_id, 0) + 1
    session['cart'] = cart
    session['cart_total'] = sum(cart.values())
    return jsonify({'total_items': session['cart_total']})

@app.route('/profile')
def profile():
    return redirect("login.html")

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


    
def recalculate_cart():
    """Helper function to recalculate cart totals and item prices."""
    cart = session.get('cart', {})
    token = kroger.get_auth_token()
    products = kroger.get_hot_products(token)

    cart_items = [
        {**p, "quantity": cart[str(p["id"])]}
        for p in products if str(p["id"]) in cart
    ]

    subtotal = sum(item["price"] * item["quantity"] for item in cart_items)
    tax = subtotal * 0.0863
    total = subtotal + tax
    total = max(0, total)

    item_prices = {str(p["id"]): p["price"] * cart[str(p["id"])] for p in products if str(p["id"]) in cart}

    return jsonify({
        'subtotal': subtotal,
        'tax': tax,
        'total': total,
        'itemPrices': item_prices
    })
    
@app.route('/clear_cart')
def clear_cart():
    session.pop('cart', None)
    session['cart_total'] = 0
    return redirect(url_for('home'))

@app.route('/update_quantity/<product_id>', methods=['POST'])
def update_quantity(product_id):
    try:
        data = request.get_json()
        new_quantity = int(data.get('quantity', 1))
        cart = session.get('cart', {})

        if product_id in cart:
            if new_quantity > 0:
                cart[product_id] = new_quantity
            else:
                cart.pop(product_id)

        session['cart'] = cart
        return recalculate_cart()
    except Exception as e:
        app.logger.error(f"Error updating quantity: {e}")
        return jsonify({'error': 'An error occurred'}), 500

@app.route('/delete_item/<product_id>', methods=['POST'])
def delete_item(product_id):
    try:
        cart = session.get('cart', {})
        if product_id in cart:
            cart.pop(product_id)
        session['cart'] = cart
        return recalculate_cart()
    except Exception as e:
        app.logger.error(f"Error deleting item: {e}")
        return jsonify({'error': 'An error occurred'}), 500

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

    print(f"Cart items: {cart_items}")
    print(f"Subtotal: {subtotal}, Tax: {tax}, Total: {total}, Coupon: {session.get('coupon', None)}")

    return render_template(
        'checkout.html',
        cart=cart_items,
        subtotal=subtotal,
        tax=tax,
        total=total,
        coupon=session.get('coupon', None),  
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

@app.route("/login.html", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html', header="Log In", redirect="login.html", otherurl="register.html", otherpage="Register an Account")
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
                return "ok"
            else:
                return "wrong credentials"
        else:
            return "user does not exist"

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

if __name__ == "__main__": 
    app.run(debug=True)