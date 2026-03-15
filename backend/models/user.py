from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from core.database import Base


class User(Base):
    __tablename__ = "users"

    id          = Column(Integer, primary_key=True, index=True)
    username    = Column(String(150), unique=True, nullable=False, index=True)
    email       = Column(String(254), unique=True, nullable=False)
    password    = Column(String(255), nullable=False) 
    role        = Column(String(20),  nullable=False, default="PUBLIC")
    team_name   = Column(String(200), nullable=True)
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())