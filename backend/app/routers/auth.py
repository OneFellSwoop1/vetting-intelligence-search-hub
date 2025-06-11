"""Authentication and user management routes."""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from ..user_management import (
    UserManager, UserRegistration, UserLogin, UserPreferences,
    user_manager, get_current_user, get_current_user_optional,
    check_user_rate_limit, require_role, get_user_ip, UserProfile
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register")
async def register_user(
    registration: UserRegistration,
    request: Request
) -> Dict[str, Any]:
    """Register a new user account."""
    try:
        # Get user IP for logging
        user_ip = get_user_ip(request)
        
        # Register user
        result = user_manager.register_user(registration)
        
        logger.info(f"User registration successful: {registration.username} from {user_ip}")
        
        return {
            "success": True,
            "message": "User registered successfully",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error for {registration.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )

@router.post("/login")
async def login_user(
    login: UserLogin,
    request: Request
) -> Dict[str, Any]:
    """Authenticate user and return access token."""
    try:
        # Get user IP for logging
        user_ip = get_user_ip(request)
        
        # Authenticate user
        result = user_manager.authenticate_user(login)
        
        logger.info(f"User login successful: {login.username} from {user_ip}")
        
        return {
            "success": True,
            "message": "Login successful",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for {login.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )

@router.post("/logout")
async def logout_user(
    user: UserProfile = Depends(get_current_user)
) -> Dict[str, Any]:
    """Logout current user and invalidate token."""
    try:
        # In a full implementation, you'd invalidate the token
        # For now, just log the logout
        logger.info(f"User logout: {user.username}")
        
        return {
            "success": True,
            "message": "Logout successful"
        }
        
    except Exception as e:
        logger.error(f"Logout error for {user.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.get("/me")
async def get_current_user_info(
    user: UserProfile = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current user information and statistics."""
    try:
        user_stats = user_manager.get_user_stats(user)
        
        return {
            "success": True,
            "data": user_stats
        }
        
    except Exception as e:
        logger.error(f"Error getting user info for {user.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )

@router.get("/profile")
async def get_user_profile(
    user: UserProfile = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get detailed user profile information."""
    return {
        "success": True,
        "data": {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "rate_limit_tier": user.rate_limit_tier,
            "preferences": user.preferences,
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "is_active": user.is_active
        }
    }

@router.put("/profile")
async def update_user_profile(
    preferences: UserPreferences,
    user: UserProfile = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update user profile preferences."""
    try:
        # Update user preferences
        user.preferences.update(preferences.dict(exclude_unset=True))
        
        logger.info(f"Profile updated for user: {user.username}")
        
        return {
            "success": True,
            "message": "Profile updated successfully",
            "data": {
                "preferences": user.preferences
            }
        }
        
    except Exception as e:
        logger.error(f"Profile update error for {user.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )

@router.get("/usage")
async def get_usage_stats(
    user: UserProfile = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """Get current user's usage statistics and rate limits."""
    try:
        stats = user_manager.get_user_stats(user)
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting usage stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage statistics"
        )

@router.get("/rate-limits")
async def get_rate_limits(
    user: UserProfile = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """Get rate limit information for current user tier."""
    from ..user_management import RateLimitConfig
    
    tier_config = RateLimitConfig.TIERS.get(
        user.rate_limit_tier, 
        RateLimitConfig.TIERS["guest"]
    )
    
    return {
        "success": True,
        "data": {
            "tier": user.rate_limit_tier,
            "limits": tier_config,
            "user_type": user.role
        }
    }

@router.post("/upgrade-tier")
async def request_tier_upgrade(
    target_tier: str,
    user: UserProfile = Depends(get_current_user)
) -> Dict[str, Any]:
    """Request an upgrade to a higher tier (placeholder for payment integration)."""
    from ..user_management import RateLimitConfig
    
    if target_tier not in RateLimitConfig.TIERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tier requested"
        )
    
    # In a real implementation, this would integrate with a payment system
    logger.info(f"Tier upgrade requested: {user.username} -> {target_tier}")
    
    return {
        "success": True,
        "message": f"Tier upgrade request received for {target_tier}. "
                   f"Please contact support to complete the upgrade.",
        "data": {
            "current_tier": user.rate_limit_tier,
            "requested_tier": target_tier,
            "contact": "support@vetting-intelligence.com"
        }
    }

# Admin routes (require elevated permissions)
@router.get("/admin/users")
async def list_all_users(
    user: UserProfile = Depends(require_role("enterprise"))
) -> Dict[str, Any]:
    """List all users (admin only)."""
    try:
        users_data = []
        for u in user_manager.users.values():
            user_stats = user_manager.get_user_stats(u)
            users_data.append(user_stats)
        
        return {
            "success": True,
            "data": {
                "total_users": len(users_data),
                "users": users_data
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user list"
        )

@router.patch("/admin/users/{user_id}/tier")
async def update_user_tier(
    user_id: str,
    new_tier: str,
    admin_user: UserProfile = Depends(require_role("enterprise"))
) -> Dict[str, Any]:
    """Update a user's tier (admin only)."""
    from ..user_management import RateLimitConfig
    
    if new_tier not in RateLimitConfig.TIERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tier"
        )
    
    target_user = user_manager.users.get(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    old_tier = target_user.rate_limit_tier
    target_user.rate_limit_tier = new_tier
    
    logger.info(f"Tier updated by {admin_user.username}: {target_user.username} {old_tier} -> {new_tier}")
    
    return {
        "success": True,
        "message": f"User tier updated successfully",
        "data": {
            "user_id": user_id,
            "username": target_user.username,
            "old_tier": old_tier,
            "new_tier": new_tier
        }
    }

@router.get("/admin/stats")
async def get_system_stats(
    admin_user: UserProfile = Depends(require_role("enterprise"))
) -> Dict[str, Any]:
    """Get system-wide user statistics (admin only)."""
    try:
        total_users = len(user_manager.users)
        
        # Count users by tier
        tier_counts = {}
        role_counts = {}
        
        for user in user_manager.users.values():
            tier_counts[user.rate_limit_tier] = tier_counts.get(user.rate_limit_tier, 0) + 1
            role_counts[user.role] = role_counts.get(user.role, 0) + 1
        
        return {
            "success": True,
            "data": {
                "total_users": total_users,
                "active_users": sum(1 for u in user_manager.users.values() if u.is_active),
                "tier_distribution": tier_counts,
                "role_distribution": role_counts,
                "active_tokens": len(user_manager.user_tokens)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system statistics"
        ) 