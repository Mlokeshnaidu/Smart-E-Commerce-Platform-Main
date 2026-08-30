from fastapi import Depends, HTTPException, status

from models.user import UserRole
from core.deps import get_current_user


def require_roles(*allowed_roles: UserRole):
    def role_checker(current_user=Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return role_checker
