from flask import Flask, render_template, redirect, url_for, session, request, jsonify

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Fake products to test
products = [
    {"id": 1, "name": "Apples", "price": 1.2},
    {"id": 2, "name": "Bananas", "price": 0.5},
    {"id": 3, "name": "Milk", "price": 2.0},
    {"id": 4, "name": "Bread", "price": 1.5},
]

@app.route('/')
def home():
    return render_template('home.html', products=products)

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
    return render_template('profile.html')

@app.route('/cart')
def cart():
    cart = session.get('cart', {})
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

if __name__ == '__main__':
    app.run(debug=True)