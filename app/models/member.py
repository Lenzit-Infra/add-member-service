# app/models/member.py
from sqlalchemy import Column, Integer, String, BigInteger, Boolean, Enum, Text, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
from app.models.common import MemberStatus # Import Enum

class Member(Base):
    __tablename__ = 'members'

    user_id = Column(BigInteger, primary_key=True) # Telegram User ID
    access_hash = Column(BigInteger, nullable=False)
    
    # Profile Attributes (Scraped Details)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    phone = Column(String, nullable=True) 
    
    # Technical & Safety Flags
    is_bot = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    is_scam = Column(Boolean, default=False)
    is_fake = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    photo_count = Column(Integer, default=0) # The number of profile photos
    
    # Our Analytics
    status = Column(Enum(MemberStatus), default=MemberStatus.UNKNOWN)
    quality_score = Column(Integer, default=0) # Calculated score (0-100)
    
    # Privacy Check (Crucial for "Can I add this user?")
    # True = Privacy Restricted (Cannot Add), False = Open, NULL = Unknown
    has_privacy_restriction = Column(Boolean, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships (defined in logs.py)