from flask import Flask 
from flask import render_template 
from flask import request
from flask import redirect
from flask import session
from flask import Flask, render_template, redirect, url_for, session, request, jsonify
import mariadb
import sys
import bcrypt

import kroger
  
# creates a Flask application 
app = Flask(__name__) 
app.secret_key = 'supersecretkey'


# Fake products to test
#products = [
#    {"id": 1, "name": "Apples", "price": 1.2},
#    {"id": 2, "name": "Bananas", "price": 0.5},
#    {"id": 3, "name": "Milk", "price": 2.0},
#    {"id": 4, "name": "Bread", "price": 1.5},
#]

@app.route('/')
def home():
    token = kroger.get_auth_token()
    products = kroger.get_hot_products(token)
    username = "Guest"
    if session.get("user"):
        username = session.get("user")
    return render_template('home.html', products=products, username = username)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_id = str(request.json['product_id'])
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
    cart = session.get('cart', {})
    token = kroger.get_auth_token()
    products = kroger.get_hot_products(token)
    cart_items = [{**p, "quantity": cart[str(p["id"])]} for p in products if str(p["id"]) in cart]
    subtotal = sum(item["price"] * item["quantity"] for item in cart_items)
    tax = subtotal * 0.0863
    total = subtotal + tax
    return render_template('cart.html', cart=cart_items, subtotal=subtotal, tax=tax, total=total)

@app.route('/clear_cart')
def clear_cart():
    session.pop('cart', None)
    session['cart_total'] = 0
    return redirect(url_for('home'))
 

@app.route("/login.html", methods = ['GET', 'POST'])
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
        
@app.route("/register.html", methods = ['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('login.html', header="Sign Up", redirect="register.html", otherurl="login.html", otherpage="Log in (Existing account)")
    elif  request.method == 'POST':
        data = request.form
        
        conn = dbconnect()
        cur = conn.cursor()
        
        username = data["user"]

        pw = data["pass"]

        # converting password to array of bytes 
        bytes = pw.encode('utf-8') 
        
        # generating the salt 
        salt = bcrypt.gensalt()
        salttxt = salt.decode("utf-8")
        
        # Hashing the password 
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
        
        #row = cur.fetchone()

@app.route("/search")
def searchProducts():
    return render_template('search.html')    
        
def dbconnect():
    # Connect to MariaDB Platform
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

    # Get Cursor
    return conn
    
def dbdisconnect():
    cur.close()
    conn.close()
  
# run the application 
if __name__ == "__main__": 
    app.run(debug=True)
