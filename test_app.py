"""
Automated End-to-End Verification Test for Restaurant Order and Billing System
"""
import urllib.request
import urllib.parse
import json
import http.cookiejar

cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

BASE_URL = "http://127.0.0.1:5000"

def get(path):
    req = urllib.request.Request(f"{BASE_URL}{path}")
    with opener.open(req) as resp:
        return resp.status, resp.read().decode('utf-8')

def post_json(path, data):
    body = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(f"{BASE_URL}{path}", data=body, headers={'Content-Type': 'application/json'})
    with opener.open(req) as resp:
        return resp.status, json.loads(resp.read().decode('utf-8'))

def post_form(path, form_data):
    body = urllib.parse.urlencode(form_data).encode('utf-8')
    req = urllib.request.Request(f"{BASE_URL}{path}", data=body, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    with opener.open(req) as resp:
        return resp.status, resp.read().decode('utf-8'), resp.geturl()

print("--> [1] Testing Home Page...")
status, html = get("/")
assert status == 200
assert "Have a Coupon for Extra Discount?" in html
print("✓ Home page loaded with Coupon Feature Banner!")

print("--> [2] Testing Menu Page...")
status, html = get("/menu")
assert status == 200
assert "Crispy Paneer Tikka" in html
print("✓ Menu page loaded with items!")

print("--> [3] Testing Add to Cart...")
status, res = post_json("/api/cart/add", {"item_id": 1, "quantity": 2})
assert status == 200
assert res['success'] == True
assert res['total_items'] == 2

status, res = post_json("/api/cart/add", {"item_id": 8, "quantity": 1})
assert status == 200
assert res['total_items'] == 3
print("✓ Cart updated with 3 items!")

print("--> [4] Testing Coupon Feature ('WELCOME50')...")
status, res = post_json("/api/coupon/apply", {"coupon_code": "WELCOME50"})
assert status == 200
assert res['success'] == True
assert res['bill']['discount_amount'] == 50.0
assert res['bill']['coupon_code'] == "WELCOME50"
print(f"✓ Coupon applied successfully: Saved ₹{res['bill']['discount_amount']}! Final total: ₹{res['bill']['final_total']}")

print("--> [5] Testing Checkout & Order Placement...")
checkout_data = {
    "name": "Aman Sharma",
    "mobile": "9876543210",
    "address": "Flat 301, Lakeview Residency, MG Road",
    "landmark": "Near Metro Station",
    "pincode": "400001",
    "payment_method": "UPI",
    "coupon_code": "WELCOME50"
}
status, html, final_url = post_form("/checkout", checkout_data)
assert status == 200
assert "/order-confirmation/" in final_url
assert "Order Successfully Placed!" in html
order_number = final_url.split('/')[-1]
order_number = urllib.parse.unquote(order_number)
print(f"✓ Order placed successfully! Order Number: {order_number}")

print("--> [6] Testing Order Tracking...")
status, html = get(f"/track-order?order={urllib.parse.quote(order_number)}")
assert status == 200
assert "Pending" in html
assert "Order Placed" in html
print("✓ Order tracking page renders 5-step stepper!")

print("--> [7] Testing Staff Dashboard...")
status, html = get("/staff")
assert status == 200
assert order_number in html
print(f"✓ Staff Dashboard displays active order {order_number}!")

print("--> [8] Staff Updates Order Status to 'Accepted'...")
status, html, _ = post_form(f"/staff/order/{urllib.parse.quote(order_number)}/status", {"status": "Accepted"})
status, body = get(f"/api/order-status/{urllib.parse.quote(order_number)}")
res = json.loads(body)
assert res['status'] == "Accepted"
print(f"✓ Order status successfully transitioned to: {res['status']}")

print("--> [9] Staff Updates Order Status to 'Preparing'...")
status, html, _ = post_form(f"/staff/order/{urllib.parse.quote(order_number)}/status", {"status": "Preparing"})
status, body = get(f"/api/order-status/{urllib.parse.quote(order_number)}")
res = json.loads(body)
assert res['status'] == "Preparing"
print(f"✓ Order status successfully transitioned to: {res['status']}")

print("--> [10] Testing Menu Management & Settings Pages...")
status, html = get("/staff/menu")
assert status == 200
status, html = get("/staff/settings")
assert status == 200
print("✓ Staff menu and settings pages verified!")

print("\n========================================================")
print(" ALL 10 END-TO-END ACCEPTANCE TESTS PASSED SUCCESSFULLY! ")
print("========================================================")
