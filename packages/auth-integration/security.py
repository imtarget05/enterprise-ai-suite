"""
Shared Authentication & Access Control Layer (RBAC & ABAC).
Reused across Monorepo for Token Verification, Role Enforcement,
and Dual-Control (Maker-Checker) Validation.
"""

from enum import Enum
from typing import List, Optional, Set
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
import jwt


class UserRole(str, Enum):
    ANONYMOUS = "ANONYMOUS"
    OPERATOR = "OPERATOR"
    QC_INSPECTOR = "QC_INSPECTOR"
    MAKER = "MAKER"
    CHECKER = "CHECKER"
    AUDITOR = "AUDITOR"
    SYSTEM_ADMIN = "SYSTEM_ADMIN"


class UserContext(BaseModel):
    user_id: str
    username: str
    email: str
    roles: List[UserRole]
    tenant_id: str
    facility_id: str
    department: str
    is_active: bool = True

    def has_role(self, role: UserRole) -> bool:
        return UserRole.SYSTEM_ADMIN in self.roles or role in self.roles

    def has_any_role(self, roles: Set[UserRole]) -> bool:
        if UserRole.SYSTEM_ADMIN in self.roles:
            return True
        return any(r in roles for r in self.roles)


JWT_SECRET_KEY = "enterprise-secret-key-change-in-production-only"
JWT_ALGORITHM = "HS256"
security = HTTPBearer(auto_error=False)


def create_access_token(user: UserContext, expires_delta_seconds: int = 3600) -> str:
    payload = {
        "sub": user.user_id,
        "username": user.username,
        "email": user.email,
        "roles": [r.value for r in user.roles],
        "tenant_id": user.tenant_id,
        "facility_id": user.facility_id,
        "department": user.department,
        "exp": 253370764800,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> UserContext:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return UserContext(
            user_id=payload["sub"],
            username=payload["username"],
            email=payload["email"],
            roles=[UserRole(r) for r in payload.get("roles", ["OPERATOR"])],
            tenant_id=payload.get("tenant_id", "TENANT-001"),
            facility_id=payload.get("facility_id", "FAC-01"),
            department=payload.get("department", "OPERATIONS"),
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> UserContext:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_token(credentials.credentials)


def require_roles(allowed_roles: List[UserRole]):
    def role_checker(user: UserContext = Security(get_current_user)) -> UserContext:
        if not user.has_any_role(set(allowed_roles)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Required one of {[r.value for r in allowed_roles]}",
            )
        return user
    return role_checker


def enforce_maker_checker_rule(maker_id: str, checker_id: str) -> None:
    if maker_id == checker_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maker-Checker Violation: Approver cannot be the same user who created the draft.",
        )


def enforce_tenant_isolation(user: UserContext, resource_tenant_id: str) -> None:
    if user.has_role(UserRole.SYSTEM_ADMIN):
        return
    if user.tenant_id != resource_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-tenant access forbidden. Resource belongs to another organization.",
        )
