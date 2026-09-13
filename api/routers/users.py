from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..core.images import (
    ALLOWED_AVATAR_CONTENT_TYPES,
    compress_avatar,
    decode_image_base64,
)
from ..models.user import User
from ..schemas.user import AvatarUpload, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(User).offset(skip).limit(limit).all()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can only update your own account")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")
    db.refresh(current_user)
    return current_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can only delete your own account")
    db.delete(current_user)
    db.commit()
    return None


@router.put("/me/avatar", response_model=UserResponse)
def upload_avatar(
    payload: AvatarUpload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.content_type not in ALLOWED_AVATAR_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported content type; allowed: {sorted(ALLOWED_AVATAR_CONTENT_TYPES)}",
        )
    raw = decode_image_base64(payload.data)
    current_user.avatar = compress_avatar(raw)
    current_user.avatar_content_type = payload.content_type
    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/me/avatar", response_model=UserResponse)
def delete_avatar(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.avatar = None
    current_user.avatar_content_type = None
    db.commit()
    db.refresh(current_user)
    return current_user