"""User management and authentication system for Vetting Intelligence Search Hub."""

import os
import logging
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass

import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr

from .cache import cache_service

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token authentication
security = HTTPBearer()

@dataclass
class UserProfile:
    """User profile data structure."""
    user_id: str
    username: str
    email: Optional[str]
    role: str
    preferences: Dict[str, Any]
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool
    rate_limit_tier: str

class UserRegistration(BaseModel):
    """User registration request model."""
    username: str
    email: EmailStr
    password: str
    organization: Optional[str] = None

class UserLogin(BaseModel):
    """User login request model."""
    username: str
    password: str

class UserPreferences(BaseModel):
    """User preferences model."""
    default_sources: Optional[List[str]] = None
    default_jurisdiction: Optional[str] = None
    notifications_enabled: bool = True
    search_history_enabled: bool = True
    export_format: str = "json"
    results_per_page: int = 50

class RateLimitConfig:
    """Rate limiting configuration for different user tiers."""
    
    TIERS = {
        "guest": {
            "requests_per_hour": 50,
            "requests_per_day": 200,
            "concurrent_searches": 2,
            "export_limit": 100
        },
        "registered": {
            "requests_per_hour": 200,
            "requests_per_day": 1000,
            "concurrent_searches": 5,
            "export_limit": 1000
        },
        "premium": {
            "requests_per_hour": 1000,
            "requests_per_day": 10000,
            "concurrent_searches": 10,
            "export_limit": 10000
        },
        "enterprise": {
            "requests_per_hour": -1,  # Unlimited
            "requests_per_day": -1,
            "concurrent_searches": 20,
            "export_limit": -1
        }
    }

class UserManager:
    """Comprehensive user management system."""
    
    def __init__(self):
        self.users: Dict[str, UserProfile] = {}
        self.user_tokens: Dict[str, str] = {}  # token -> user_id
        self.rate_limits: Dict[str, Dict[str, Any]] = {}
        self.active_sessions: Dict[str, List[str]] = {}  # user_id -> [session_ids]
        
        # Initialize guest user
        self.guest_user = UserProfile(
            user_id="guest",
            username="guest",
            email=None,
            role="guest",
            preferences={},
            created_at=datetime.now(),
            last_login=None,
            is_active=True,
            rate_limit_tier="guest"
        )
    
    def hash_password(self, password: str) -> str:
        """Hash a password securely."""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, user_id: str, username: str) -> str:
        """Create a JWT access token."""
        expires_delta = timedelta(hours=JWT_EXPIRE_HOURS)
        expire = datetime.utcnow() + expires_delta
        
        to_encode = {
            "sub": user_id,
            "username": username,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        token = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        self.user_tokens[token] = user_id
        
        return token
    
    def verify_token(self, token: str) -> Optional[str]:
        """Verify a JWT token and return user_id."""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            user_id = payload.get("sub")
            
            if user_id and token in self.user_tokens:
                return user_id
                
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
        except jwt.JWTError as e:
            logger.warning(f"Token verification failed: {e}")
        
        return None
    
    def register_user(self, registration: UserRegistration) -> Dict[str, Any]:
        """Register a new user."""
        # Check if username already exists
        if any(user.username == registration.username for user in self.users.values()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Generate user ID
        user_id = hashlib.sha256(
            f"{registration.username}{registration.email}{time.time()}".encode()
        ).hexdigest()[:16]
        
        # Create user profile
        user_profile = UserProfile(
            user_id=user_id,
            username=registration.username,
            email=registration.email,
            role="registered",
            preferences={
                "organization": registration.organization,
                **UserPreferences().dict()
            },
            created_at=datetime.now(),
            last_login=None,
            is_active=True,
            rate_limit_tier="registered"
        )
        
        # Hash password and store (in production, use database)
        hashed_password = self.hash_password(registration.password)
        cache_service.redis_client.setex(
            f"user_password:{user_id}",
            86400 * 30,  # 30 days
            hashed_password
        )
        
        # Store user profile
        self.users[user_id] = user_profile
        
        # Create access token
        token = self.create_access_token(user_id, registration.username)
        
        logger.info(f"User registered: {registration.username} (ID: {user_id})")
        
        return {
            "user_id": user_id,
            "username": registration.username,
            "token": token,
            "expires_in": JWT_EXPIRE_HOURS * 3600,
            "role": user_profile.role,
            "rate_limit_tier": user_profile.rate_limit_tier
        }
    
    def authenticate_user(self, login: UserLogin) -> Dict[str, Any]:
        """Authenticate a user and return token."""
        # Find user by username
        user = None
        for u in self.users.values():
            if u.username == login.username:
                user = u
                break
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Verify password
        stored_password = cache_service.redis_client.get(f"user_password:{user.user_id}")
        if not stored_password or not self.verify_password(login.password, stored_password.decode()):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Update last login
        user.last_login = datetime.now()
        
        # Create access token
        token = self.create_access_token(user.user_id, user.username)
        
        logger.info(f"User authenticated: {login.username}")
        
        return {
            "user_id": user.user_id,
            "username": user.username,
            "token": token,
            "expires_in": JWT_EXPIRE_HOURS * 3600,
            "role": user.role,
            "rate_limit_tier": user.rate_limit_tier
        }
    
    def get_user_from_token(self, token: str) -> Optional[UserProfile]:
        """Get user profile from token."""
        user_id = self.verify_token(token)
        if user_id:
            return self.users.get(user_id)
        return None
    
    def check_rate_limit(self, user: UserProfile, request_type: str = "search") -> bool:
        """Check if user is within rate limits."""
        tier_config = RateLimitConfig.TIERS.get(user.rate_limit_tier, RateLimitConfig.TIERS["guest"])
        
        current_time = time.time()
        hour_key = f"rate_limit:{user.user_id}:hour:{int(current_time // 3600)}"
        day_key = f"rate_limit:{user.user_id}:day:{int(current_time // 86400)}"
        
        # Check hourly limit
        if tier_config["requests_per_hour"] > 0:
            hourly_count = cache_service.redis_client.get(hour_key)
            if hourly_count and int(hourly_count) >= tier_config["requests_per_hour"]:
                return False
        
        # Check daily limit
        if tier_config["requests_per_day"] > 0:
            daily_count = cache_service.redis_client.get(day_key)
            if daily_count and int(daily_count) >= tier_config["requests_per_day"]:
                return False
        
        # Increment counters
        cache_service.redis_client.incr(hour_key)
        cache_service.redis_client.expire(hour_key, 3600)
        cache_service.redis_client.incr(day_key)
        cache_service.redis_client.expire(day_key, 86400)
        
        return True
    
    def get_user_stats(self, user: UserProfile) -> Dict[str, Any]:
        """Get user statistics and usage info."""
        current_time = time.time()
        hour_key = f"rate_limit:{user.user_id}:hour:{int(current_time // 3600)}"
        day_key = f"rate_limit:{user.user_id}:day:{int(current_time // 86400)}"
        
        hourly_usage = cache_service.redis_client.get(hour_key) or 0
        daily_usage = cache_service.redis_client.get(day_key) or 0
        
        tier_config = RateLimitConfig.TIERS.get(user.rate_limit_tier, RateLimitConfig.TIERS["guest"])
        
        return {
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role,
            "rate_limit_tier": user.rate_limit_tier,
            "usage": {
                "hourly_requests": int(hourly_usage),
                "daily_requests": int(daily_usage),
                "hourly_limit": tier_config["requests_per_hour"],
                "daily_limit": tier_config["requests_per_day"]
            },
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "created_at": user.created_at.isoformat(),
            "is_active": user.is_active
        }

# Global user manager instance
user_manager = UserManager()

# FastAPI dependencies
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserProfile:
    """FastAPI dependency to get current authenticated user."""
    token = credentials.credentials
    user = user_manager.get_user_from_token(token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

async def get_current_user_optional(
    request: Request
) -> UserProfile:
    """FastAPI dependency to get current user or guest."""
    auth_header = request.headers.get("Authorization")
    
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        user = user_manager.get_user_from_token(token)
        if user:
            return user
    
    # Return guest user if no valid token
    return user_manager.guest_user

async def check_user_rate_limit(user: UserProfile = Depends(get_current_user_optional)) -> UserProfile:
    """FastAPI dependency to check rate limits."""
    if not user_manager.check_rate_limit(user):
        tier_config = RateLimitConfig.TIERS.get(user.rate_limit_tier, RateLimitConfig.TIERS["guest"])
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Tier: {user.rate_limit_tier}, "
                   f"Hourly limit: {tier_config['requests_per_hour']}, "
                   f"Daily limit: {tier_config['requests_per_day']}"
        )
    
    return user

# Utility functions
def require_role(required_role: str):
    """Decorator to require specific user role."""
    def decorator(user: UserProfile = Depends(get_current_user)):
        role_hierarchy = {"guest": 0, "registered": 1, "premium": 2, "enterprise": 3}
        
        user_level = role_hierarchy.get(user.role, 0)
        required_level = role_hierarchy.get(required_role, 999)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {required_role} role or higher"
            )
        
        return user
    return decorator

def get_user_ip(request: Request) -> str:
    """Extract user IP address from request."""
    # Check for forwarded headers (if behind proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct connection
    return request.client.host if request.client else "unknown" 