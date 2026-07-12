"""End-to-end workflow test for Restaurant RPS."""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request

import httpx

BASE = "http://127.0.0.1:8001"
FRONTEND = "http://localhost:5173"

PREDICT = {
    "date": "2026-07-12",
    "hour": 17,
    "temperature": 31.0,
    "rainfall": 0,
    "promotion": True,
    "is_holiday": False,
    "previous_hour_customers": 72,
    "previous_day_customers": 1400,
    "walk_in_customers": 45,
    "online_reservations": 18,
    "takeaway_orders": 10,
    "delivery_orders": 14,
    "kitchen_load": 0.62,
    "table_utilization": 0.58,
    "supplier_delay_days": 0,
    "local_event": "E2E Test",
    "average_order_value": 480,
    "is_weekend": True,
}


def main() -> int:
    report: dict = {"steps": [], "passed": True, "issues": []}

    def step(name: str, ok: bool, detail: str = "", data=None) -> None:
        report["steps"].append({"step": name, "ok": ok, "detail": detail, "data": data})
        if not ok:
            report["passed"] = False
            report["issues"].append({"step": name, "detail": detail})

    with httpx.Client(base_url=BASE, timeout=300.0) as c:
        r = c.get("/health")
        step("Pre-check: backend health", r.status_code == 200, f"status={r.status_code}")

        dash0 = c.get("/dashboard/latest")
        model0 = c.get("/model/current")
        hist0 = c.get("/feedback/history", params={"limit": 5})
        step(
            "1. Dashboard load",
            dash0.status_code == 200 and model0.status_code == 200,
            f"dashboard={dash0.status_code}, model={model0.status_code}, history={hist0.status_code}",
        )
        initial_model_version = model0.json().get("version_label") if model0.status_code == 200 else None

        r = c.post("/forecast/predict", json=PREDICT)
        pred = r.json() if r.status_code == 200 else {}
        prediction_id = pred.get("prediction_id")
        predicted_customers = pred.get("predicted_customers")
        step(
            "2. Forecast prediction",
            r.status_code == 200 and bool(prediction_id) and bool(predicted_customers),
            f"id={prediction_id}, customers={predicted_customers}, confidence={pred.get('confidence')}",
        )

        latest_fc = c.get("/forecast/latest")
        fc_data = latest_fc.json() if latest_fc.status_code == 200 else {}
        step(
            "2b. Forecast persisted to DB",
            latest_fc.status_code == 200 and fc_data.get("prediction_id") == prediction_id,
            f"latest prediction_id={fc_data.get('prediction_id')}",
        )

        staff_payload = {"predicted_customers": predicted_customers, "prediction_id": prediction_id}
        r = c.post("/recommendation/staff", json=staff_payload)
        staff = r.json() if r.status_code == 200 else {}
        step(
            "3. Generate staff plan",
            r.status_code == 200 and bool(staff.get("total_staff")),
            f"total_staff={staff.get('total_staff')}, cost={staff.get('staff_cost')}, id={staff.get('id')}",
        )

        staff_latest = c.get("/staff/latest")
        sl = staff_latest.json() if staff_latest.status_code == 200 else {}
        step(
            "3b. Staff plan persisted",
            staff_latest.status_code == 200 and sl.get("predicted_customers") == predicted_customers,
            f"latest staff predicted={sl.get('predicted_customers')}",
        )

        inv_payload = {
            "predicted_customers": predicted_customers,
            "prediction_id": prediction_id,
            "safety_stock_rate": 0.15,
            "supplier_lead_time_days": 2,
            "wastage_rate": 0.05,
            "current_inventory": {},
        }
        r = c.post("/recommendation/inventory", json=inv_payload)
        inv = r.json() if r.status_code == 200 else {}
        step(
            "4. Generate inventory plan",
            r.status_code == 200 and bool(inv.get("ingredient_count")),
            f"ingredients={inv.get('ingredient_count')}, cost={inv.get('inventory_cost')}, id={inv.get('id')}",
        )

        inv_latest = c.get("/inventory/latest")
        il = inv_latest.json() if inv_latest.status_code == 200 else {}
        step(
            "4b. Inventory plan persisted",
            inv_latest.status_code == 200 and il.get("predicted_customers") == predicted_customers,
            f"latest inventory predicted={il.get('predicted_customers')}",
        )

        r2 = c.post("/forecast/predict", json={**PREDICT, "hour": 18})
        fb_pred = r2.json() if r2.status_code == 200 else {}
        fb_prediction_id = fb_pred.get("prediction_id")
        fb_predicted = fb_pred.get("predicted_customers")
        actual = (fb_predicted or 70) + 3
        latest_forecast_id = fb_prediction_id

        r = c.post(
            "/feedback",
            json={
                "prediction_id": fb_prediction_id,
                "actual_customers": actual,
                "comments": "E2E workflow test feedback",
            },
        )
        fb = r.json() if r.status_code == 201 else {}
        step(
            "5. Submit manager feedback",
            r.status_code == 201 and fb.get("prediction_id") == fb_prediction_id,
            f"actual={actual}, mape={fb.get('mape')}, production={fb.get('production_model')}",
        )

        time.sleep(1)
        model1 = c.get("/model/current")
        m1 = model1.json() if model1.status_code == 200 else {}
        versions = c.get("/model/versions")
        vlist = versions.json() if versions.status_code == 200 else []
        retrained = model1.status_code == 200 and bool(m1.get("version_label")) and fb.get("retraining") is not None
        step(
            "6. Model retraining",
            retrained,
            f"before={initial_model_version}, after={m1.get('version_label')}, versions={len(vlist)}, new_accuracy={fb.get('new_accuracy')}",
        )

        acc = c.get("/model/accuracy")
        a = acc.json() if acc.status_code == 200 else {}
        analytics_ok = (
            model1.status_code == 200
            and acc.status_code == 200
            and versions.status_code == 200
            and a.get("feedback_count", 0) >= 1
        )
        step(
            "7. Analytics update",
            analytics_ok,
            f"feedback_count={a.get('feedback_count')}, current={m1.get('version_label')}, latest_model={a.get('latest_model')}",
        )

        hist = c.get("/feedback/history", params={"limit": 500})
        hlist = hist.json() if hist.status_code == 200 else []
        found_fb = any(
            x.get("id") == fb_prediction_id and x.get("actual_customers") == actual for x in hlist
        )
        found_fc = any(x.get("id") == prediction_id for x in hlist)
        step(
            "8. Prediction history",
            hist.status_code == 200 and found_fb and found_fc,
            f"history_rows={len(hlist)}, forecast_in_history={found_fc}, feedback_in_history={found_fb}",
        )

        refresh = {
            "dashboard": c.get("/dashboard/latest"),
            "forecast": c.get("/forecast/latest"),
            "staff": c.get("/staff/latest"),
            "inventory": c.get("/inventory/latest"),
            "model": c.get("/model/current"),
            "accuracy": c.get("/model/accuracy"),
            "history": c.get("/feedback/history", params={"limit": 500}),
        }

        rd = refresh["dashboard"].json() if refresh["dashboard"].status_code == 200 else {}
        rf = refresh["forecast"].json() if refresh["forecast"].status_code == 200 else {}
        rs = refresh["staff"].json() if refresh["staff"].status_code == 200 else {}
        ri = refresh["inventory"].json() if refresh["inventory"].status_code == 200 else {}
        rm = refresh["model"].json() if refresh["model"].status_code == 200 else {}

        persist_checks = [
            (
                "forecast/latest",
                refresh["forecast"].status_code == 200,
                rf.get("prediction_id") == latest_forecast_id,
            ),
            ("staff/latest", refresh["staff"].status_code == 200, rs.get("predicted_customers") == predicted_customers),
            (
                "inventory/latest",
                refresh["inventory"].status_code == 200,
                ri.get("predicted_customers") == predicted_customers,
            ),
            (
                "dashboard/latest",
                refresh["dashboard"].status_code == 200,
                rd.get("forecast") == predicted_customers,
            ),
            ("model/current", refresh["model"].status_code == 200, rm.get("version_label") == m1.get("version_label")),
            ("feedback in history", refresh["history"].status_code == 200, found_fb),
        ]

        for name, status_ok, data_ok in persist_checks:
            step(f"9. Refresh persist: {name}", status_ok and data_ok, f"api_ok={status_ok}, data_ok={data_ok}")

    for route in ["/", "/forecast", "/staff", "/inventory", "/feedback", "/analytics", "/history"]:
        try:
            with urllib.request.urlopen(FRONTEND + route, timeout=8) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
                ok = resp.status == 200 and "root" in body
                step(f"9b. Frontend route {route}", ok, f"HTTP {resp.status}")
        except (urllib.error.URLError, TimeoutError) as exc:
            step(f"9b. Frontend route {route}", False, str(exc))

    print(json.dumps(report, indent=2, default=str))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
