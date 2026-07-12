"""Verify Phase 3 dataset APIs."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["DATABASE_URL"] = "sqlite:///./verify_test.db"

from fastapi.testclient import TestClient

from app.main import create_app

app = create_app()


def main() -> None:
    with TestClient(app) as client:
        info = client.get("/dataset/info")
        print(f"GET /dataset/info -> {info.status_code}")
        print(info.json())

        regen = client.post("/dataset/regenerate")
        print(f"\nPOST /dataset/regenerate -> {regen.status_code}")
        print(regen.json())

        assert info.status_code == 200
        assert regen.status_code == 201
        assert regen.json()["total_rows"] >= 10_000
        print("\nPhase 3 dataset APIs verified.")


if __name__ == "__main__":
    main()
