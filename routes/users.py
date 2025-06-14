

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from common.db.config import get_db
from models.models import User
from schemas.users import UserCreate, UserUpdate, UserOut  # Assuming you have these schemas defined

users_router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


# Generate crud endpoints for User model
@users_router.get("", response_model=List[UserOut])  # Assuming you have a UserOut schema defined
def get_users(db: Session = Depends(get_db)):  # Assuming you have a session dependency

    users = db.query(User).all()
    if not users:
        return {"message": "No users found"}
    return users

@users_router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"message": "User not found"}
    return user

@users_router.post("", response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    print("Creating user:", user.dict())
    user_obj = User(**user.dict())
    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)
    if not user_obj:
        return {"message": "User creation failed"}
    return user_obj



@users_router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: UUID, user: UserUpdate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.id == user_id).first()
    if not existing_user:
        return {"message": "User not found"}
    for key, value in user.dict().items():
        setattr(existing_user, key, value)
    db.commit()
    db.refresh(existing_user)
    return existing_user


@users_router.delete("/{user_id}", response_model=dict)
def delete_user(user_id: UUID, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"message": "User not found"}
    db.delete(user)
    db.commit()
    return {"message": f"User with ID {user_id} deleted"}
# Include the users router in the main application