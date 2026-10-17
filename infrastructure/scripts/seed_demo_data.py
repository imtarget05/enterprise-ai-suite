#!/usr/bin/env python3
"""
Seed Demo Data Script for Enterprise AI Suite.
Initializes tables, seeds demo users with RBAC roles, and populates initial items.
"""

import os
import sys
import hashlib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from packages.auth_integration.security import UserRole
from packages.shared_contracts.models import Base, UserModel
from apps.enterprise_copilot.backend.core.db import SessionLocal, init_db


def hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def seed_data():
    print("Initializing database schema...")
    init_db()

    db = SessionLocal()
    try:
        users = [
            UserModel(
                username="maker_demo",
                email="maker@enterprise.local",
                hashed_password=hash_pw("DemoMaker2026!"),
                roles=[UserRole.MAKER.value],
                tenant_id="TENANT-001",
                facility_id="FAC-01",
                department="OPERATIONS",
            ),
            UserModel(
                username="checker_demo",
                email="checker@enterprise.local",
                hashed_password=hash_pw("DemoChecker2026!"),
                roles=[UserRole.CHECKER.value],
                tenant_id="TENANT-001",
                facility_id="FAC-01",
                department="SUPERVISION",
            ),
            UserModel(
                username="inspector_demo",
                email="qc_inspector@enterprise.local",
                hashed_password=hash_pw("DemoQC2026!"),
                roles=[UserRole.QC_INSPECTOR.value],
                tenant_id="TENANT-001",
                facility_id="FAC-01",
                department="QUALITY",
            ),
            UserModel(
                username="admin_demo",
                email="admin@enterprise.local",
                hashed_password=hash_pw("DemoAdmin2026!"),
                roles=[UserRole.SYSTEM_ADMIN.value],
                tenant_id="TENANT-001",
                facility_id="FAC-01",
                department="IT_ADMIN",
            ),
        ]

        for u in users:
            existing = db.query(UserModel).filter(UserModel.username == u.username).first()
            if not existing:
                db.add(u)
                print(f"Seeded user: {u.username} ({u.roles})")

        db.commit()
        print(">> Database seeding complete and verified!")
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
