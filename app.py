"""
Restaurant Order and Billing System
Based on PRD v1.0 specifications.
Backend: Flask (Python)
Storage: File-based JSON (data/menu.json, data/orders.json, data/settings.json)
"""

import os
import json
import re
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, flash
)

app = Flask(__name__)
app.secret_key = os.urandom(24)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

MENU_FILE = os.path.join(DATA_DIR, 'menu.json')
ORDERS_FILE = os.path.join(DATA_DIR, 'orders.json')
SETTINGS_FILE = os.path.join(DATA_DIR, 'settings.json')


# -------------------------------------------------------------
# File Storage Helpers
# -------------------------------------------------------------
def load_json(filepath, default_value=None):
    if not os.path.exists(filepath):
        if default_value is not None:
            save_json(filepath, default_value)
            return default_value
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return default_value if default_value is not None else []


def save_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_menu():
    return load_json(MENU_FILE, [])


def save_menu(menu):
    save_json(MENU_FILE, menu)


def get_orders():
    return load_json(ORDERS_FILE, [])


def save_orders(orders):
    save_json(ORDERS_FILE, orders)


def get_settings():
    default_settings = {
        "restaurant_name": "Saffron & Spice Bistro",
        "tagline": "Authentic Flavors, Delivered Fresh to Your Door",
        "phone": "+91 98765 43210",
        "address": "45 Culinary Boulevard, Food District",
        "currency_symbol": "₹",
        "tax_rate": 5.0,
        "service_charge": 30.0,
        "next_order_number": 1026,
        "categories": [
            "Starters", "Main Course", "Pizza", "Burger",
            "Sandwich", "Biryani", "Beverages", "Desserts"
        ],
        "coupons": [
            {
                "code": "WELCOME50",
                "type": "fixed",
                "value": 50,
                "min_order": 200,
                "description": "Flat ₹50 OFF on orders above ₹200",
                "active": True
            },
            {
                "code": "FEAST20",
                "type": "percentage",
                "value": 20,
                "max_discount": 100,
                "min_order": 300,
                "description": "20% OFF up to ₹100 on orders above ₹300",
                "active": True
            },
            {
                "code": "SUPER100",
                "type": "fixed",
                "value": 100,
                "min_order": 600,
                "description": "Flat ₹100 OFF on orders above ₹600",
                "active": True
            },
            {
                "code": "LUCKY10",
                "type": "percentage",
                "value": 10,
                "max_discount": 75,
                "min_order": 150,
                "description": "10% Extra Discount on orders above ₹150",
                "active": True
            }
        ]
    }
    return load_json(SETTINGS_FILE, default_settings)


def save_settings(settings):
    save_json(SETTINGS_FILE, settings)


# -------------------------------------------------------------
# Billing and Coupon Calculation Engine
# -------------------------------------------------------------
def compute_bill(cart_items, coupon_code=None):
    """
    PRD Section 9:
    Final Total = Subtotal + Tax + Service Charge - Discount
    A discount must not produce an invalid negative payable amount.
    """
    settings = get_settings()
    tax_rate = float(settings.get('tax_rate', 5.0))
    service_charge = float(settings.get('service_charge', 30.0))

    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    tax_amount = round(subtotal * (tax_rate / 100.0), 2)

    discount_amount = 0.0
    applied_coupon = None
    coupon_message = ""

    if coupon_code:
        coupon_code_clean = coupon_code.strip().upper()
        coupons = settings.get('coupons', [])
        found_coupon = next(
            (c for c in coupons if c.get('code', '').upper() == coupon_code_clean and c.get('active', True)),
            None
        )

        if not found_coupon:
            coupon_message = f"Invalid or expired coupon code: '{coupon_code}'"
        else:
            min_order = float(found_coupon.get('min_order', 0))
            if subtotal < min_order:
                coupon_message = f"Coupon '{coupon_code_clean}' requires a minimum order of ₹{min_order:.2f}."
            else:
                applied_coupon = found_coupon
                c_type = found_coupon.get('type', 'fixed')
                c_val = float(found_coupon.get('value', 0))

                if c_type == 'percentage':
                    discount_amount = round(subtotal * (c_val / 100.0), 2)
                    max_disc = found_coupon.get('max_discount')
                    if max_disc is not None and discount_amount > float(max_disc):
                        discount_amount = float(max_disc)
                else:
                    discount_amount = c_val

                # Discount cannot exceed subtotal
                if discount_amount > subtotal:
                    discount_amount = float(subtotal)
                coupon_message = f"Coupon '{coupon_code_clean}' applied! You saved ₹{discount_amount:.2f}."

    # Final Total = Subtotal + Tax + Service Charge - Discount
    final_total = max(0.0, round(subtotal + tax_amount + service_charge - discount_amount, 2))

    return {
        'subtotal': round(subtotal, 2),
        'tax_rate': tax_rate,
        'tax_amount': tax_amount,
        'service_charge': round(service_charge, 2),
        'discount_amount': round(discount_amount, 2),
        'final_total': final_total,
        'coupon_code': applied_coupon['code'] if applied_coupon else None,
        'coupon_message': coupon_message,
        'coupon_valid': bool(applied_coupon)
    }


def get_cart_details():
    cart = session.get('cart', {})
    menu = {str(item['id']): item for item in get_menu()}
    cart_items = []
    
    for item_id_str, qty in cart.items():
        if item_id_str in menu and qty > 0:
            item = menu[item_id_str]
            cart_items.append({
                'id': item['id'],
                'name': item['name'],
                'price': float(item['price']),
                'quantity': int(qty),
                'amount': round(float(item['price']) * int(qty), 2),
                'photo': item.get('photo', ''),
                'category': item.get('category', ''),
                'available': item.get('available', True)
            })
    return cart_items


# -------------------------------------------------------------
# Context Processor for Templates
# -------------------------------------------------------------
@app.context_processor
def inject_globals():
    settings = get_settings()
    cart = session.get('cart', {})
    total_cart_items = sum(cart.values())
    return {
        'settings': settings,
        'total_cart_items': total_cart_items,
        'active_coupon': session.get('applied_coupon')
    }


# -------------------------------------------------------------
# Customer Routes
# -------------------------------------------------------------
@app.route('/')
def home():
    menu = get_menu()
    settings = get_settings()
    # Featured items: available items across categories
    featured_items = [item for item in menu if item.get('available', True)][:6]
    coupons = [c for c in settings.get('coupons', []) if c.get('active', True)]
    return render_template(
        'index.html',
        featured_items=featured_items,
        categories=settings.get('categories', []),
        coupons=coupons
    )


@app.route('/menu')
def menu_page():
    menu = get_menu()
    settings = get_settings()
    selected_category = request.args.get('category', 'all').strip()
    search_query = request.args.get('q', '').strip().lower()

    filtered_menu = menu
    if selected_category and selected_category.lower() != 'all':
        filtered_menu = [i for i in filtered_menu if i.get('category', '').lower() == selected_category.lower()]

    if search_query:
        filtered_menu = [
            i for i in filtered_menu
            if search_query in i.get('name', '').lower() or search_query in i.get('description', '').lower()
        ]

    # Group by category for menu layout
    categories = settings.get('categories', [])
    return render_template(
        'menu.html',
        menu=filtered_menu,
        all_categories=categories,
        selected_category=selected_category,
        search_query=search_query
    )


@app.route('/cart')
def cart_page():
    cart_items = get_cart_details()
    coupon_code = session.get('applied_coupon')
    bill = compute_bill(cart_items, coupon_code)
    settings = get_settings()
    available_coupons = [c for c in settings.get('coupons', []) if c.get('active', True)]

    return render_template(
        'cart.html',
        cart_items=cart_items,
        bill=bill,
        coupons=available_coupons
    )


@app.route('/api/cart/add', methods=['POST'])
def api_cart_add():
    data = request.get_json() or {}
    item_id = str(data.get('item_id'))
    quantity = int(data.get('quantity', 1))

    if quantity <= 0:
        return jsonify({'success': False, 'message': 'Quantity must be greater than zero.'}), 400

    menu = {str(item['id']): item for item in get_menu()}
    if item_id not in menu:
        return jsonify({'success': False, 'message': 'Item not found in menu.'}), 404

    if not menu[item_id].get('available', True):
        return jsonify({'success': False, 'message': 'This item is currently unavailable.'}), 400

    cart = session.get('cart', {})
    current_qty = cart.get(item_id, 0)
    cart[item_id] = current_qty + quantity
    session['cart'] = cart
    session.modified = True

    total_items = sum(cart.values())
    return jsonify({
        'success': True,
        'message': f"Added {menu[item_id]['name']} to your cart.",
        'total_items': total_items,
        'item_qty': cart[item_id]
    })


@app.route('/api/cart/update', methods=['POST'])
def api_cart_update():
    data = request.get_json() or {}
    item_id = str(data.get('item_id'))
    action = data.get('action')  # 'increase', 'decrease', 'remove', 'set'
    value = data.get('value')

    cart = session.get('cart', {})
    if item_id in cart:
        if action == 'increase':
            cart[item_id] += 1
        elif action == 'decrease':
            cart[item_id] -= 1
            if cart[item_id] <= 0:
                del cart[item_id]
        elif action == 'remove':
            del cart[item_id]
        elif action == 'set':
            qty = int(value or 1)
            if qty > 0:
                cart[item_id] = qty
            else:
                del cart[item_id]

    session['cart'] = cart
    session.modified = True

    cart_items = get_cart_details()
    coupon_code = session.get('applied_coupon')
    bill = compute_bill(cart_items, coupon_code)

    return jsonify({
        'success': True,
        'cart_items': cart_items,
        'bill': bill,
        'total_items': sum(cart.values()),
        'item_qty': cart.get(item_id, 0)
    })


@app.route('/api/coupon/apply', methods=['POST'])
def api_coupon_apply():
    data = request.get_json() or {}
    coupon_code = data.get('coupon_code', '').strip()

    if not coupon_code:
        return jsonify({'success': False, 'message': 'Please enter a coupon code.'}), 400

    cart_items = get_cart_details()
    if not cart_items:
        return jsonify({'success': False, 'message': 'Your cart is empty. Add food items first.'}), 400

    bill = compute_bill(cart_items, coupon_code)
    if bill['coupon_valid']:
        session['applied_coupon'] = bill['coupon_code']
        session.modified = True
        return jsonify({
            'success': True,
            'message': bill['coupon_message'],
            'bill': bill
        })
    else:
        return jsonify({
            'success': False,
            'message': bill['coupon_message'] or 'Invalid coupon code.',
            'bill': bill
        }), 400


@app.route('/api/coupon/remove', methods=['POST'])
def api_coupon_remove():
    session.pop('applied_coupon', None)
    session.modified = True
    cart_items = get_cart_details()
    bill = compute_bill(cart_items, None)
    return jsonify({
        'success': True,
        'message': 'Coupon removed.',
        'bill': bill
    })


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart_items = get_cart_details()

    if request.method == 'GET':
        if not cart_items:
            flash('Your cart is empty. Please add items to your cart before proceeding to checkout.', 'warning')
            return redirect(url_for('menu_page'))

        coupon_code = session.get('applied_coupon')
        bill = compute_bill(cart_items, coupon_code)
        settings = get_settings()
        coupons = [c for c in settings.get('coupons', []) if c.get('active', True)]

        return render_template(
            'checkout.html',
            cart_items=cart_items,
            bill=bill,
            coupons=coupons
        )

    # POST - Order Placement
    if not cart_items:
        flash('Cannot place an order with an empty cart.', 'danger')
        return redirect(url_for('menu_page'))

    # PRD Section 7: Collect customer name, mobile number, full delivery address, landmark, and PIN code
    customer_name = request.form.get('name', '').strip()
    mobile = request.form.get('mobile', '').strip()
    address = request.form.get('address', '').strip()
    landmark = request.form.get('landmark', '').strip()
    pincode = request.form.get('pincode', '').strip()
    payment_method = request.form.get('payment_method', 'Cash').strip()
    coupon_code_form = request.form.get('coupon_code', '').strip()

    # Validations per PRD Section 20
    errors = []
    if not customer_name:
        errors.append("Customer name is required.")

    # Valid Indian mobile number (10 digits)
    clean_mobile = re.sub(r'[\s\-\+]', '', mobile)
    if not clean_mobile or not clean_mobile.isdigit() or len(clean_mobile) < 10:
        errors.append("Please enter a valid 10-digit mobile number.")

    if not address:
        errors.append("Full delivery address is required.")
    if not landmark:
        errors.append("Landmark is required for accurate delivery.")
    if not pincode or not pincode.isdigit() or len(pincode) != 6:
        errors.append("Please enter a valid 6-digit PIN code.")

    allowed_payments = ['Cash', 'UPI', 'Card', 'Other']
    if payment_method not in allowed_payments:
        payment_method = 'Cash'

    # Check unavailable items (PRD Section 21: Business Rule 1)
    unavailable_items = [item['name'] for item in cart_items if not item.get('available', True)]
    if unavailable_items:
        errors.append(f"The following items are currently unavailable: {', '.join(unavailable_items)}. Please remove them from your cart.")

    if errors:
        for error in errors:
            flash(error, 'danger')
        coupon_code = coupon_code_form or session.get('applied_coupon')
        bill = compute_bill(cart_items, coupon_code)
        settings = get_settings()
        coupons = [c for c in settings.get('coupons', []) if c.get('active', True)]
        return render_template(
            'checkout.html',
            cart_items=cart_items,
            bill=bill,
            coupons=coupons,
            form_data=request.form
        )

    # Compute final verified bill
    coupon_to_use = coupon_code_form or session.get('applied_coupon')
    bill = compute_bill(cart_items, coupon_to_use)

    # Generate unique order number (PRD Section 10: e.g. #1026)
    settings = get_settings()
    next_num = settings.get('next_order_number', 1026)
    order_number = f"#{next_num}"
    settings['next_order_number'] = next_num + 1
    save_settings(settings)

    # Create order object
    new_order = {
        'order_number': order_number,
        'created_at': datetime.now().strftime('%Y-%m-%d %I:%M %p'),
        'customer': {
            'name': customer_name,
            'mobile': clean_mobile,
            'address': address,
            'landmark': landmark,
            'pincode': pincode
        },
        'items': [
            {
                'id': item['id'],
                'name': item['name'],
                'price': item['price'],
                'quantity': item['quantity'],
                'amount': item['amount']
            } for item in cart_items
        ],
        'subtotal': bill['subtotal'],
        'tax_rate': bill['tax_rate'],
        'tax_amount': bill['tax_amount'],
        'service_charge': bill['service_charge'],
        'coupon_code': bill['coupon_code'],
        'discount_amount': bill['discount_amount'],
        'final_total': bill['final_total'],
        'payment_method': payment_method,
        'status': 'Pending',
        'active': True
    }

    orders = get_orders()
    orders.insert(0, new_order)
    save_orders(orders)

    # Clear session cart and applied coupon
    session.pop('cart', None)
    session.pop('applied_coupon', None)
    session.modified = True

    return redirect(url_for('order_confirmation', order_number=order_number))


@app.route('/order-confirmation/<order_number>')
def order_confirmation(order_number):
    clean_order_num = order_number.strip()
    if not clean_order_num.startswith('#'):
        clean_order_num = '#' + clean_order_num

    orders = get_orders()
    order = next((o for o in orders if o.get('order_number') == clean_order_num), None)

    if not order:
        flash(f"Order {order_number} not found.", 'danger')
        return redirect(url_for('home'))

    return render_template('order_confirmation.html', order=order)


@app.route('/track')
@app.route('/track-order')
def track_order():
    order_number = request.args.get('order', '').strip()
    order = None

    if order_number:
        clean_order_num = order_number
        if not clean_order_num.startswith('#'):
            clean_order_num = '#' + clean_order_num

        orders = get_orders()
        order = next((o for o in orders if o.get('order_number') == clean_order_num), None)
        if not order:
            flash(f"Order '{order_number}' could not be found. Please double check your order number.", 'warning')

    return render_template('order_status.html', order=order, search_query=order_number)


@app.route('/api/order-status/<order_number>')
def api_order_status(order_number):
    clean_order_num = order_number.strip()
    if not clean_order_num.startswith('#'):
        clean_order_num = '#' + clean_order_num

    orders = get_orders()
    order = next((o for o in orders if o.get('order_number') == clean_order_num), None)

    if not order:
        return jsonify({'success': False, 'message': 'Order not found'}), 404

    return jsonify({
        'success': True,
        'order_number': order['order_number'],
        'status': order['status'],
        'active': order.get('active', True),
        'created_at': order.get('created_at', ''),
        'customer_name': order.get('customer', {}).get('name', ''),
        'final_total': order.get('final_total', 0)
    })


# -------------------------------------------------------------
# Restaurant Staff Routes (No Login Required as per PRD)
# -------------------------------------------------------------
@app.route('/staff')
@app.route('/staff/dashboard')
def staff_dashboard():
    orders = get_orders()
    status_filter = request.args.get('filter', 'active').strip()

    if status_filter == 'active':
        # PRD Section 12 & 14: Only active orders displayed by default
        display_orders = [o for o in orders if o.get('active', True) and o.get('status') not in ['Completed', 'Rejected']]
    elif status_filter == 'all':
        display_orders = orders
    else:
        display_orders = [o for o in orders if o.get('status', '').lower() == status_filter.lower()]

    # Stats for staff overview
    active_count = len([o for o in orders if o.get('active', True) and o.get('status') not in ['Completed', 'Rejected']])
    pending_count = len([o for o in orders if o.get('status') == 'Pending'])
    preparing_count = len([o for o in orders if o.get('status') == 'Preparing'])
    ready_count = len([o for o in orders if o.get('status') == 'Ready'])
    completed_today = len([o for o in orders if o.get('status') == 'Completed'])

    return render_template(
        'staff_dashboard.html',
        orders=display_orders,
        status_filter=status_filter,
        active_count=active_count,
        pending_count=pending_count,
        preparing_count=preparing_count,
        ready_count=ready_count,
        completed_today=completed_today
    )


@app.route('/staff/order/<order_number>/status', methods=['POST'])
def staff_update_order_status(order_number):
    new_status = request.form.get('status', '').strip()
    valid_statuses = ['Pending', 'Accepted', 'Preparing', 'Ready', 'Completed', 'Rejected']

    if new_status not in valid_statuses:
        flash("Invalid status specified.", 'danger')
        return redirect(url_for('staff_dashboard'))

    clean_order_num = order_number.strip()
    if not clean_order_num.startswith('#'):
        clean_order_num = '#' + clean_order_num

    orders = get_orders()
    updated = False
    for o in orders:
        if o.get('order_number') == clean_order_num:
            o['status'] = new_status
            if new_status in ['Completed', 'Rejected']:
                o['active'] = False
            else:
                o['active'] = True
            updated = True
            break

    if updated:
        save_orders(orders)
        flash(f"Order {clean_order_num} updated to {new_status}.", 'success')
    else:
        flash(f"Order {clean_order_num} was not found.", 'danger')

    return redirect(url_for('staff_dashboard'))


@app.route('/staff/menu')
def staff_menu():
    menu = get_menu()
    settings = get_settings()
    categories = settings.get('categories', [])
    return render_template('manage_menu.html', menu=menu, categories=categories)


@app.route('/staff/menu/add', methods=['POST'])
def staff_menu_add():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    price_raw = request.form.get('price', '0').strip()
    category = request.form.get('category', '').strip()
    photo = request.form.get('photo', '').strip()
    available = 'available' in request.form

    try:
        price = float(price_raw)
        if price < 0:
            flash("Price cannot be negative.", 'danger')
            return redirect(url_for('staff_menu'))
    except ValueError:
        flash("Invalid price value.", 'danger')
        return redirect(url_for('staff_menu'))

    if not name:
        flash("Item name is required.", 'danger')
        return redirect(url_for('staff_menu'))

    menu = get_menu()
    new_id = max([item['id'] for item in menu], default=0) + 1

    if not photo:
        photo = "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=600&auto=format&fit=crop&q=80"

    new_item = {
        'id': new_id,
        'name': name,
        'description': description,
        'price': price,
        'category': category or 'Main Course',
        'photo': photo,
        'available': available
    }

    menu.append(new_item)
    save_menu(menu)
    flash(f"Menu item '{name}' added successfully!", 'success')
    return redirect(url_for('staff_menu'))


@app.route('/staff/menu/edit/<int:item_id>', methods=['POST'])
def staff_menu_edit(item_id):
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    price_raw = request.form.get('price', '0').strip()
    category = request.form.get('category', '').strip()
    photo = request.form.get('photo', '').strip()
    available = 'available' in request.form

    try:
        price = float(price_raw)
        if price < 0:
            flash("Price cannot be negative.", 'danger')
            return redirect(url_for('staff_menu'))
    except ValueError:
        flash("Invalid price value.", 'danger')
        return redirect(url_for('staff_menu'))

    menu = get_menu()
    for item in menu:
        if item['id'] == item_id:
            item['name'] = name or item['name']
            item['description'] = description
            item['price'] = price
            item['category'] = category or item['category']
            if photo:
                item['photo'] = photo
            item['available'] = available
            break

    save_menu(menu)
    flash(f"Menu item updated successfully!", 'success')
    return redirect(url_for('staff_menu'))


@app.route('/staff/menu/delete/<int:item_id>', methods=['POST'])
def staff_menu_delete(item_id):
    menu = get_menu()
    menu = [item for item in menu if item['id'] != item_id]
    save_menu(menu)
    flash("Menu item deleted.", 'info')
    return redirect(url_for('staff_menu'))


@app.route('/staff/menu/toggle-availability/<int:item_id>', methods=['POST'])
def staff_menu_toggle_availability(item_id):
    menu = get_menu()
    for item in menu:
        if item['id'] == item_id:
            item['available'] = not item.get('available', True)
            save_menu(menu)
            status_txt = "Available" if item['available'] else "Unavailable"
            return jsonify({'success': True, 'available': item['available'], 'status_txt': status_txt})

    return jsonify({'success': False, 'message': 'Item not found'}), 404


@app.route('/staff/settings', methods=['GET', 'POST'])
def staff_settings():
    settings = get_settings()

    if request.method == 'POST':
        tax_rate_raw = request.form.get('tax_rate', '5.0').strip()
        service_charge_raw = request.form.get('service_charge', '30.0').strip()
        restaurant_name = request.form.get('restaurant_name', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()

        try:
            tax_rate = float(tax_rate_raw)
            if tax_rate < 0:
                flash("Tax percentage cannot be negative.", 'danger')
                return redirect(url_for('staff_settings'))
        except ValueError:
            flash("Invalid tax rate.", 'danger')
            return redirect(url_for('staff_settings'))

        try:
            service_charge = float(service_charge_raw)
            if service_charge < 0:
                flash("Service charge cannot be negative.", 'danger')
                return redirect(url_for('staff_settings'))
        except ValueError:
            flash("Invalid service charge.", 'danger')
            return redirect(url_for('staff_settings'))

        settings['tax_rate'] = tax_rate
        settings['service_charge'] = service_charge
        if restaurant_name:
            settings['restaurant_name'] = restaurant_name
        if phone:
            settings['phone'] = phone
        if address:
            settings['address'] = address

        save_settings(settings)
        flash("Settings updated successfully!", 'success')
        return redirect(url_for('staff_settings'))

    return render_template('settings.html', settings=settings)


@app.route('/staff/coupons/add', methods=['POST'])
def staff_add_coupon():
    code = request.form.get('code', '').strip().upper()
    c_type = request.form.get('type', 'fixed')
    value_raw = request.form.get('value', '0').strip()
    min_order_raw = request.form.get('min_order', '0').strip()
    max_discount_raw = request.form.get('max_discount', '').strip()
    description = request.form.get('description', '').strip()

    if not code:
        flash("Coupon code is required.", 'danger')
        return redirect(url_for('staff_settings'))

    try:
        val = float(value_raw)
        min_ord = float(min_order_raw or 0)
        max_disc = float(max_discount_raw) if max_discount_raw else None
        if val <= 0:
            flash("Coupon discount value must be greater than zero.", 'danger')
            return redirect(url_for('staff_settings'))
    except ValueError:
        flash("Invalid numerical values for coupon.", 'danger')
        return redirect(url_for('staff_settings'))

    settings = get_settings()
    coupons = settings.get('coupons', [])

    # Check duplicate
    if any(c.get('code', '').upper() == code for c in coupons):
        flash(f"Coupon code '{code}' already exists.", 'warning')
        return redirect(url_for('staff_settings'))

    coupons.append({
        'code': code,
        'type': c_type,
        'value': val,
        'min_order': min_ord,
        'max_discount': max_disc,
        'description': description or f"Special {val}{'%' if c_type == 'percentage' else ' off'} Discount",
        'active': True
    })

    settings['coupons'] = coupons
    save_settings(settings)
    flash(f"Coupon '{code}' added successfully!", 'success')
    return redirect(url_for('staff_settings'))


@app.route('/staff/coupons/delete/<code>', methods=['POST'])
def staff_delete_coupon(code):
    settings = get_settings()
    coupons = [c for c in settings.get('coupons', []) if c.get('code', '').upper() != code.upper()]
    settings['coupons'] = coupons
    save_settings(settings)
    flash(f"Coupon '{code}' removed.", 'info')
    return redirect(url_for('staff_settings'))


@app.route('/staff/coupons/toggle/<code>', methods=['POST'])
def staff_toggle_coupon(code):
    settings = get_settings()
    for c in settings.get('coupons', []):
        if c.get('code', '').upper() == code.upper():
            c['active'] = not c.get('active', True)
            break
    save_settings(settings)
    flash(f"Coupon '{code}' status updated.", 'success')
    return redirect(url_for('staff_settings'))


# -------------------------------------------------------------
# Run Server
# -------------------------------------------------------------
if __name__ == '__main__':
    # Ensure data directory and files exist
    os.makedirs(DATA_DIR, exist_ok=True)
    get_menu()
    get_orders()
    get_settings()
    print("==================================================")
    print(" Saffron & Spice Bistro - Server Starting...")
    print(" Customer Site:   http://127.0.0.1:5000/")
    print(" Staff Dashboard: http://127.0.0.1:5000/staff")
    print(" Menu Management: http://127.0.0.1:5000/staff/menu")
    print(" Settings:        http://127.0.0.1:5000/staff/settings")
    print("==================================================")
    app.run(debug=True, port=5000)
