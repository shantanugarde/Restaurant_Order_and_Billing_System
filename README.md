# Restaurant Order and Billing System

A complete web-based restaurant order and billing web application built with **Python** and **Flask**, adhering strictly to the **PRD v1.0** specifications and featuring file-based JSON storage, real-time order tracking, staff dashboard, and an interactive **Discount Coupon System**.

---

## 🌟 Key Features

### 1. Customer Ordering Flow
- **Interactive Food Menu**: Browse delicious dishes by category (Starters, Main Course, Pizza, Burger, Sandwich, Biryani, Beverages, Desserts) with live search and availability badges.
- **Shopping Cart Management**: Add food items, adjust quantities, calculate item totals, and view real-time subtotal.
- **Delivery Checkout**: Collects Customer Name, 10-digit Mobile Number, Full Delivery Address, Landmark, and 6-digit PIN code.
- **Payment Method Selection**: Record selection for Cash on Delivery, UPI / QR Scan, Credit / Debit Card, or Other (record-only as per PRD).
- **Automated Bill Calculation**:
  $$\text{Final Total} = \text{Subtotal} + \text{Tax} + \text{Service Charge} - \text{Discount}$$
- **Order Placement**: Assigns a unique order number (e.g., `#1026`), renders a celebratory receipt, and directs customers to live tracking.
- **Customer Order Tracking (No Login Required)**: Visual 5-step timeline tracking:
  $$\text{Order Placed} \rightarrow \text{Order Accepted} \rightarrow \text{Preparing} \rightarrow \text{Ready} \rightarrow \text{Completed}$$
  *(or Alternative: $\text{Pending} \rightarrow \text{Rejected}$)* with live background auto-sync!

---

### 2. Exclusive Feature: "Do you have any coupon for extra discount?"
Honoring both the user prompt and the original `project.py` script:
- **Interactive Prompting**: Both on Cart and Checkout pages, the system prominently asks: *"Do you have any coupon for extra discount?"*
- **Click-to-Apply Offers**:
  - `WELCOME50` — Flat ₹50 OFF on orders above ₹200
  - `FEAST20` — 20% OFF up to ₹100 on orders above ₹300
  - `SUPER100` — Flat ₹100 OFF on orders above ₹600
  - `LUCKY10` — 10% Extra Discount on orders above ₹150
- **Lucky Digit Coupon (from original terminal script)**: Customers can pick a digit (0 to 9) to claim a surprise lucky discount!
- **Zero Negative Payable Protection**: Validates discounts so that total payable amount never becomes negative.
- **Staff Coupon Management**: Restaurant staff can add new coupons, toggle active status, or delete codes directly from settings.

---

### 3. Restaurant Staff Portal (No Login Required as per PRD)
- **Active Orders Dashboard (`/staff`)**: View incoming order tickets displaying Customer Info, Delivery Address, Items ordered, Bill breakdown, Payment method, and current status.
- **Quick Status Workflow**:
  - For `Pending`: **`[Accept]`** and **`[Reject]`** one-click buttons.
  - For `Accepted`: **`[Start Preparing]`**
  - For `Preparing`: **`[Mark Ready for Delivery]`**
  - For `Ready`: **`[Mark Completed]`**
- **Menu Management (`/staff/menu`)**:
  - Add new dishes with photos, category, and pricing.
  - Edit existing items.
  - Delete items.
  - Instant One-Click **Available / Unavailable Toggle** (Unavailable items are immediately blocked from customer cart and checkout).
- **Settings & Taxes (`/staff/settings`)**:
  - Configure Tax Percentage (% GST).
  - Configure Service & Packaging Charge (₹).
  - Manage and create discount coupons.

---

## 📁 Project Structure (PRD Section 16)

```text
amine/
├── app.py                     # Main Flask web application
├── project.py                 # Original Python CLI script
├── README.md                  # System documentation
├── data/                      # File-based JSON persistent storage
│   ├── menu.json              # Food menu catalog
│   ├── orders.json            # Customer orders and status records
│   └── settings.json          # Restaurant config, tax rate & coupons
├── static/
│   ├── css/
│   │   └── style.css          # Modern, responsive aesthetic stylesheet
│   └── js/
│       └── main.js            # Dynamic cart, coupon validation, live polling
└── templates/
    ├── base.html              # Base HTML layout with navbar & footer
    ├── index.html             # Customer landing page & featured dishes
    ├── menu.html              # Full menu with search & category filters
    ├── cart.html              # Cart review, quantity controls & coupon box
    ├── checkout.html          # Delivery details form & payment selector
    ├── order_confirmation.html# Order success screen with order #
    ├── order_status.html      # 5-step visual tracking stepper
    ├── staff_dashboard.html   # Staff active orders management
    ├── manage_menu.html       # Staff menu item CRUD & availability switch
    └── settings.html          # Staff tax, service charge & coupon management
```

---

## 🚀 Running the Application

### 1. Requirements
- Python 3.10+
- Flask (`pip install flask`)

### 2. Start the Server
Run the following command from the project directory:

```bash
python app.py
```

### 3. Access the Web Application
Open your web browser and visit:
- **Customer Website**: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
- **Full Food Menu**: [http://127.0.0.1:5000/menu](http://127.0.0.1:5000/menu)
- **Customer Order Tracking**: [http://127.0.0.1:5000/track-order](http://127.0.0.1:5000/track-order)
- **Staff Orders Dashboard**: [http://127.0.0.1:5000/staff](http://127.0.0.1:5000/staff)
- **Staff Menu Management**: [http://127.0.0.1:5000/staff/menu](http://127.0.0.1:5000/staff/menu)
- **Staff Settings & Coupons**: [http://127.0.0.1:5000/staff/settings](http://127.0.0.1:5000/staff/settings)
