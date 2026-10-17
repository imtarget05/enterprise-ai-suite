import pytest
from fastapi import HTTPException
from packages.auth_integration.security import (
    UserContext, UserRole, create_access_token, enforce_maker_checker_rule, enforce_tenant_isolation
)


def test_maker_checker_violation_raises_error():
    # User 1 tries to approve their own order
    with pytest.raises(HTTPException) as exc:
        enforce_maker_checker_rule(maker_id="user-123", checker_id="user-123")
    assert exc.value.status_code == 400
    assert "Maker-Checker Violation" in exc.value.detail


def test_maker_checker_valid_different_users():
    # Two distinct users
    enforce_maker_checker_rule(maker_id="maker-1", checker_id="checker-2")


def test_tenant_isolation_blocks_cross_tenant():
    user = UserContext(
        user_id="user-1",
        username="tenant1_user",
        email="u@tenant1.local",
        roles=[UserRole.OPERATOR],
        tenant_id="TENANT-AAA",
        facility_id="FAC-01",
        department="OPERATIONS",
    )
    with pytest.raises(HTTPException) as exc:
        enforce_tenant_isolation(user, resource_tenant_id="TENANT-BBB")
    assert exc.value.status_code == 403
    assert "Cross-tenant access forbidden" in exc.value.detail


def test_tenant_isolation_allows_admin():
    admin = UserContext(
        user_id="admin-1",
        username="admin_user",
        email="admin@corp.local",
        roles=[UserRole.SYSTEM_ADMIN],
        tenant_id="TENANT-AAA",
        facility_id="FAC-01",
        department="IT",
    )
    # Admin can inspect any tenant
    enforce_tenant_isolation(admin, resource_tenant_id="TENANT-BBB")
