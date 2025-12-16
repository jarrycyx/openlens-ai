import json
import os
from typing import Dict, List, Any, Optional
from loguru import logger
from datetime import datetime

USERS_FILE = os.path.join("outputs", "users.json")


class UserManager:
    """
    User management class, responsible for maintaining user information and points
    """
    
    def __init__(self):
        """Initialize user manager"""
        self.users_file = USERS_FILE
        self._ensure_users_file_exists()
    
    def _ensure_users_file_exists(self):
        """Ensure user file exists"""
        if not os.path.exists("outputs"):
            os.makedirs("outputs")
            
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w') as f:
                json.dump({}, f)
    
    def load_users(self) -> Dict[str, Any]:
        """Load all user information"""
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def save_users(self, users: Dict[str, Any]):
        """Save user information to file"""
        with open(self.users_file, 'w') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
    
    def add_user(self, user_id: str, email: str = "", name: str = "", initial_points: int = 100) -> bool:
        """
        Add new user
        
        Args:
            user_id: Unique user identifier
            email: User email
            name: User name
            initial_points: Initial points
            
        Returns:
            bool: Whether successfully added
        """
        users = self.load_users()
        
        # Check if user already exists
        if user_id in users:
            logger.warning(f"User {user_id} already exists")
            return False
        
        # Create new user
        users[user_id] = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "points": initial_points,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.save_users(users)
        logger.info(f"Successfully added user {user_id}")
        return True
    
    def update_user_points(self, user_id: str, points_change: int, reason: str = "") -> bool:
        """
        Update user points
        
        Args:
            user_id: User ID
            points_change: Points change amount (positive for increase, negative for decrease)
            reason: Reason for points change
            
        Returns:
            bool: Whether successfully updated
        """
        users = self.load_users()
        
        # Check if user exists
        if user_id not in users:
            logger.warning(f"User {user_id} does not exist")
            return False
        
        # Update points
        users[user_id]["points"] += points_change
        users[user_id]["updated_at"] = datetime.now().isoformat()
        
        # Add points change record
        if "points_history" not in users[user_id]:
            users[user_id]["points_history"] = []
        
        users[user_id]["points_history"].append({
            "change": points_change,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })
        
        self.save_users(users)
        logger.info(f"Updated user {user_id} points by {points_change}, new total: {users[user_id]['points']}")
        return True
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user information
        
        Args:
            user_id: User ID
            
        Returns:
            User information dictionary, returns None if user doesn't exist
        """
        users = self.load_users()
        return users.get(user_id)
    
    def get_user_points(self, user_id: str) -> Optional[int]:
        """
        Get user points
        
        Args:
            user_id: User ID
            
        Returns:
            User points, returns None if user doesn't exist
        """
        user_info = self.get_user_info(user_id)
        return user_info["points"] if user_info else None
    
    def list_all_users(self) -> List[Dict[str, Any]]:
        """
        Get list of all users
        
        Returns:
            List of all user information
        """
        users = self.load_users()
        return list(users.values())
    
    def delete_user(self, user_id: str) -> bool:
        """
        Delete user
        
        Args:
            user_id: User ID
            
        Returns:
            bool: Whether successfully deleted
        """
        users = self.load_users()
        
        if user_id not in users:
            logger.warning(f"User {user_id} does not exist")
            return False
        
        del users[user_id]
        self.save_users(users)
        logger.info(f"Successfully deleted user {user_id}")
        return True
    
    def get_top_users_by_points(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get list of users with highest points
        
        Args:
            limit: Limit on number of users to return
            
        Returns:
            List of users sorted by points in descending order
        """
        users = self.load_users()
        sorted_users = sorted(users.values(), key=lambda x: x.get("points", 0), reverse=True)
        return sorted_users[:limit]


# Global user manager instance
user_manager = UserManager()