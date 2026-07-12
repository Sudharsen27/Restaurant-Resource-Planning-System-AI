import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DATABASE_URL", "sqlite:///./verify_test.db")

from app.recommendation.cost_estimator import estimate_profit, estimate_staff_cost
from app.recommendation.inventory_engine import recommend_inventory
from app.recommendation.staff_engine import recommend_staff


class TestStaffEngine:
    def test_staff_counts_for_180_customers(self):
        staff = recommend_staff(180)
        assert staff["chef"] == 6
        assert staff["waiter"] == 9
        assert staff["kitchen_helper"] == 5
        assert staff["cashier"] == 2
        assert staff["cleaner"] == 3
        assert staff["host"] == 2
        assert staff["manager"] == 1

    def test_minimum_staff_for_low_demand(self):
        staff = recommend_staff(10)
        assert staff["chef"] >= 1
        assert staff["waiter"] >= 1
        assert staff["manager"] == 1

    def test_invalid_customers_raises(self):
        with pytest.raises(ValueError):
            recommend_staff(0)


class TestInventoryEngine:
    def test_returns_all_ingredients(self):
        items = recommend_inventory(200)
        names = {item["name"] for item in items}
        assert "Chicken" in names
        assert "Rice" in names
        assert "Coffee Powder" in names
        assert len(items) >= 10

    def test_purchase_reduced_by_current_inventory(self):
        without_stock = recommend_inventory(150)
        with_stock = recommend_inventory(150, current_inventory={"Chicken": 100, "Rice": 100})
        chicken_without = next(i for i in without_stock if i["name"] == "Chicken")
        chicken_with = next(i for i in with_stock if i["name"] == "Chicken")
        assert chicken_with["purchase"] <= chicken_without["purchase"]

    def test_higher_demand_increases_purchase(self):
        low = recommend_inventory(50)
        high = recommend_inventory(300)
        low_chicken = next(i for i in low if i["name"] == "Chicken")["purchase"]
        high_chicken = next(i for i in high if i["name"] == "Chicken")["purchase"]
        assert high_chicken > low_chicken


class TestCostEstimator:
    def test_staff_cost_positive(self):
        staff = recommend_staff(100)
        cost = estimate_staff_cost(staff)
        assert cost > 0

    def test_profit_calculation(self):
        profit = estimate_profit(200, staff_cost=10000, inventory_cost=20000, average_order_value=400)
        assert profit == 200 * 400 - 10000 - 20000
