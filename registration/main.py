from fastapi import FastAPI, HTTPException, Depends, File, UploadFile
from passlib.context import CryptContext
from .database import SessionLocal,engine
from . import models
from sqlalchemy.orm import Session
import os


app = FastAPI()


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()




models.Base.metadata.create_all(bind=engine)


@app.post("/register/")
async def register_user(
    full_name: str,
    email: str,
    password: str,
    phone: str,
    profile_picture: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    
    if db.query(models.User).filter(models.User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(models.User).filter(models.User.phone == phone).first():
        raise HTTPException(status_code=400, detail="Phone already registered")

    
    hashed_password = pwd_context.hash(password)


    db_user = models.User(full_name=full_name, email=email, hashed_password=hashed_password, phone=phone)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    if profile_picture:
        profile_picture_path = f"uploads/{db_user.id}_{profile_picture.filename}"
        os.makedirs(os.path.dirname(profile_picture_path), exist_ok=True)
        with open(profile_picture_path, "wb") as f:
            f.write(profile_picture.file.read())

        db_profile = models.Profile(user_id=db_user.id, profile_picture=profile_picture_path)
        db.add(db_profile)
        db.commit()
        db.refresh(db_profile)

    return {"message": "User registered successfully"}

@app.get("/user/{user_id}/", response_model=dict)
async def get_user_details(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    profile = db.query(models.Profile).filter(models.Profile.user_id == user_id).first()

    user_details = {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone,
    }

    if profile:
        user_details["profile_picture"] = profile.profile_picture

    return user_details