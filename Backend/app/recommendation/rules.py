"""Business rules for staff scheduling and inventory procurement."""

# --- Staff scheduling ratios ---

STAFF_RULES = {
    "waiter": {"per_customers": 20, "minimum": 1},
    "chef": {"per_customers": 30, "minimum": 1},
    "kitchen_helper": {"per_customers": 40, "minimum": 1},
    "cashier": {"per_customers": 120, "minimum": 1, "additional_every": 120},
    "cleaner": {"per_customers": 60, "minimum": 1},
    "manager": {"minimum": 1},
    "host": {"per_customers": 80, "minimum": 0},
}

# Hourly wage assumptions (INR) for cost estimation
STAFF_HOURLY_RATES = {
    "chef": 350,
    "waiter": 200,
    "kitchen_helper": 180,
    "cashier": 220,
    "cleaner": 150,
    "manager": 450,
    "host": 180,
}

SHIFT_HOURS = 8

# --- Menu mix (% of customers ordering each item) ---

MENU_MIX = {
    "Chicken Biryani": 0.18,
    "Fried Rice": 0.14,
    "Burger": 0.12,
    "Pizza": 0.11,
    "Pasta": 0.10,
    "Sandwich": 0.09,
    "Coffee": 0.08,
    "Tea": 0.10,
    "Juice": 0.08,
}

# Ingredient per serving (quantity in specified unit)
MENU_RECIPES: dict[str, dict[str, float]] = {
    "Chicken Biryani": {
        "Chicken": 0.25, "Rice": 0.20, "Oil": 0.02, "Onion": 0.05,
        "Tomato": 0.03, "Milk": 0.05, "Butter": 0.01, "Vegetables": 0.04,
    },
    "Fried Rice": {
        "Rice": 0.18, "Oil": 0.015, "Onion": 0.04, "Tomato": 0.02,
        "Vegetables": 0.06, "Butter": 0.008,
    },
    "Burger": {
        "Chicken": 0.12, "Bread": 1, "Cheese": 0.03, "Onion": 0.02,
        "Tomato": 0.02, "Oil": 0.01, "Butter": 0.005,
    },
    "Pizza": {
        "Cheese": 0.08, "Tomato": 0.05, "Onion": 0.03, "Oil": 0.01,
        "Chicken": 0.10, "Bread": 0.5, "Vegetables": 0.04,
    },
    "Pasta": {
        "Cheese": 0.05, "Tomato": 0.06, "Oil": 0.015, "Milk": 0.04,
        "Butter": 0.01, "Chicken": 0.08, "Vegetables": 0.03,
    },
    "Sandwich": {
        "Bread": 2, "Cheese": 0.02, "Tomato": 0.02, "Onion": 0.02,
        "Butter": 0.005, "Vegetables": 0.03,
    },
    "Coffee": {
        "Coffee Powder": 0.015, "Milk": 0.08, "Sugar": 0.01,
    },
    "Tea": {
        "Tea Powder": 0.008, "Milk": 0.10, "Sugar": 0.012,
    },
    "Juice": {
        "Sugar": 0.015, "Vegetables": 0.12, "Milk": 0.02,
    },
}

INGREDIENT_UNITS = {
    "Chicken": "kg",
    "Rice": "kg",
    "Oil": "L",
    "Onion": "kg",
    "Tomato": "kg",
    "Cheese": "kg",
    "Milk": "L",
    "Butter": "kg",
    "Bread": "pcs",
    "Coffee Powder": "kg",
    "Tea Powder": "kg",
    "Sugar": "kg",
    "Vegetables": "kg",
}

INGREDIENT_UNIT_PRICES = {
    "Chicken": 170,
    "Rice": 55,
    "Oil": 140,
    "Onion": 35,
    "Tomato": 40,
    "Cheese": 420,
    "Milk": 55,
    "Butter": 480,
    "Bread": 25,
    "Coffee Powder": 900,
    "Tea Powder": 600,
    "Sugar": 45,
    "Vegetables": 60,
}

INGREDIENT_SHELF_LIFE_DAYS = {
    "Chicken": 2,
    "Rice": 180,
    "Oil": 365,
    "Onion": 14,
    "Tomato": 7,
    "Cheese": 21,
    "Milk": 3,
    "Butter": 30,
    "Bread": 3,
    "Coffee Powder": 365,
    "Tea Powder": 365,
    "Sugar": 365,
    "Vegetables": 5,
}

DEFAULT_SAFETY_STOCK_RATE = 0.15
DEFAULT_WASTAGE_RATE = 0.05
AVERAGE_ORDER_VALUE = 420
