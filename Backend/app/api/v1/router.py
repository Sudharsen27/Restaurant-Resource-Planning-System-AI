"""API v1 route aggregation — all versioned domain routers."""

from fastapi import APIRouter

from app.api.analytics_bi import router as analytics_bi_router
from app.api.automation_admin import router as automation_admin_router
from app.api.auth import router as auth_router
from app.api.branches import router as branches_router
from app.api.catalog import (
    alerts_router,
    catalog_router,
    erp_inventory_router,
    grn_router,
    menu_router,
    po_router,
    recipes_router,
    transfers_router,
    txn_router,
    units_router,
)
from app.api.categories import router as categories_router
from app.api.crm_hrms import (
    attendance_router,
    crm_router,
    hrms_router,
    leaves_router,
    loyalty_router,
    payroll_router,
    reservations_router,
    shifts_router,
)
from app.api.customers import router as customers_router
from app.api.dataset import router as dataset_router
from app.api.employees import router as employees_router
from app.api.erp_dashboard import router as erp_dashboard_router
from app.api.feedback_learning import router as feedback_learning_router
from app.api.forecast import router as forecast_router
from app.api.forecast_ml import router as forecast_ml_router
from app.api.health import router as health_router
from app.api.inventory import router as inventory_router
from app.api.inventory_items import router as inventory_items_router
from app.api.latest_snapshots import router as latest_snapshots_router
from app.api.model_learning import router as model_learning_router
from app.api.notifications import router as notifications_router
from app.api.orders import pos_router, router as orders_router
from app.api.operations import (
    departments_router,
    dining_router,
    documents_router,
    ops_router,
    settings_router,
    tables_router,
)
from app.api.products import router as products_router
from app.api.recommendation import router as recommendation_router
from app.api.restaurants import router as restaurants_router
from app.api.root import router as root_router
from app.api.saas import router as saas_router
from app.api.staff import router as staff_router
from app.api.suppliers import router as suppliers_router
from app.api.warehouses import router as warehouses_router

v1_router = APIRouter()
v1_router.include_router(root_router)
v1_router.include_router(health_router)
v1_router.include_router(auth_router)
v1_router.include_router(restaurants_router)
v1_router.include_router(branches_router)
v1_router.include_router(dining_router)
v1_router.include_router(tables_router)
v1_router.include_router(departments_router)
v1_router.include_router(settings_router)
v1_router.include_router(documents_router)
v1_router.include_router(ops_router)
v1_router.include_router(categories_router)
v1_router.include_router(products_router)
v1_router.include_router(suppliers_router)
v1_router.include_router(warehouses_router)
v1_router.include_router(units_router)
v1_router.include_router(po_router)
v1_router.include_router(grn_router)
v1_router.include_router(recipes_router)
v1_router.include_router(menu_router)
v1_router.include_router(txn_router)
v1_router.include_router(alerts_router)
v1_router.include_router(transfers_router)
v1_router.include_router(catalog_router)
v1_router.include_router(erp_inventory_router)
v1_router.include_router(customers_router)
v1_router.include_router(crm_router)
v1_router.include_router(loyalty_router)
v1_router.include_router(reservations_router)
v1_router.include_router(shifts_router)
v1_router.include_router(attendance_router)
v1_router.include_router(leaves_router)
v1_router.include_router(payroll_router)
v1_router.include_router(hrms_router)
v1_router.include_router(employees_router)
v1_router.include_router(inventory_items_router)
v1_router.include_router(orders_router)
v1_router.include_router(pos_router)
v1_router.include_router(notifications_router)
v1_router.include_router(erp_dashboard_router)
v1_router.include_router(analytics_bi_router)
v1_router.include_router(automation_admin_router)
v1_router.include_router(saas_router)
v1_router.include_router(latest_snapshots_router)
v1_router.include_router(forecast_ml_router)
v1_router.include_router(forecast_router)
v1_router.include_router(staff_router)
v1_router.include_router(inventory_router)
v1_router.include_router(feedback_learning_router)
v1_router.include_router(dataset_router)
v1_router.include_router(recommendation_router)
v1_router.include_router(model_learning_router)
