from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
from app.core.exceptions import NotFoundException, ConflictException, BadRequestException


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> User:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundException("User not found")
        return user

    def get_by_email(self, email: str) -> User:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_username(self, username: str) -> User:
        return self.db.query(User).filter(User.username == username).first()

    def create(self, user_data: UserCreate) -> User:
        if self.get_by_email(user_data.email):
            raise ConflictException("Email already registered")
        if self.get_by_username(user_data.username):
            raise ConflictException("Username already taken")

        user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=get_password_hash(user_data.password),
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate(self, email: str, password: str) -> User:
        user = self.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise BadRequestException("Invalid email or password")
        return user

    def update(self, user: User, update_data: UserUpdate) -> User:
        update_dict = update_data.model_dump(exclude_unset=True)

        if "username" in update_dict:
            existing = self.get_by_username(update_dict["username"])
            if existing and existing.id != user.id:
                raise ConflictException("Username already taken")

        for key, value in update_dict.items():
            setattr(user, key, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    def change_password(self, user: User, current_password: str, new_password: str) -> None:
        if not verify_password(current_password, user.hashed_password):
            raise BadRequestException("Current password is incorrect")
        user.hashed_password = get_password_hash(new_password)
        self.db.commit()
