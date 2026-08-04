"""Regression coverage for JWT guards on legacy write routes."""

from fastapi.routing import APIRoute

from app.api import (
    dataset,
    feedback,
    feedback_learning,
    forecast,
    forecast_ml,
    inventory,
    model_learning,
    recommendation,
    staff,
)
from app.api.dependencies import get_current_user


def write_routes(router) -> list[APIRoute]:
    return [
        route
        for route in router.routes
        if isinstance(route, APIRoute)
        and route.methods.intersection({"POST", "PUT", "PATCH", "DELETE"})
    ]


def test_legacy_write_routes_require_authenticated_user():
    routers = (
        dataset.router,
        feedback.router,
        feedback_learning.router,
        forecast.router,
        forecast_ml.router,
        inventory.router,
        model_learning.router,
        recommendation.router,
        staff.router,
    )

    for router in routers:
        for route in write_routes(router):
            dependency_calls = {dependency.call for dependency in route.dependant.dependencies}
            assert get_current_user in dependency_calls, (
                f"{','.join(sorted(route.methods))} {route.path} must require JWT authentication"
            )
