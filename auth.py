import bcrypt
import re
from datetime import datetime

class AuthManager:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def validate_email(self, email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password(self, password):
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'[0-9]', password):
            return False, "Password must contain at least one number"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        return True, "Password is valid"
    
    def hash_password(self, password):
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password, hashed):
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception as e:
            return False
    
    def register_user(self, username, email, password):
        """Register new user"""
        # Validate inputs
        if not username or len(username) < 3:
            return False, "Username must be at least 3 characters long"
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Username can only contain letters, numbers, and underscores"
        
        if not self.validate_email(email):
            return False, "Invalid email format"
        
        is_valid, message = self.validate_password(password)
        if not is_valid:
            return False, message
        
        # Hash password
        password_hash = self.hash_password(password)
        
        # Create user in database
        success, result = self.db.create_user(username, email, password_hash)
        
        if success:
            return True, "Registration successful! Please login."
        else:
            return False, result
    
    def authenticate_user(self, username, password):
        """Authenticate user and return user object"""
        # Get user from database
        user = self.db.get_user_by_username(username)
        
        if not user:
            return None
        
        # Verify password
        if not self.verify_password(password, user['password_hash']):
            return None
        
        # Check if account is active
        if not user['is_active']:
            return None
        
        # Update last login
        self.db.update_last_login(user['user_id'])
        
        return user
    
    def change_password(self, user_id, old_password, new_password):
        """Change user password"""
        # Get user
        user = self.db.get_user_by_id(user_id)
        
        if not user:
            return False, "User not found"
        
        # Verify old password
        if not self.verify_password(old_password, user['password_hash']):
            return False, "Incorrect current password"
        
        # Validate new password
        is_valid, message = self.validate_password(new_password)
        if not is_valid:
            return False, message
        
        # Hash new password
        new_password_hash = self.hash_password(new_password)
        
        # Update password in database
        success = self.db.update_user_password(user_id, new_password_hash)
        
        if success:
            return True, "Password changed successfully"
        else:
            return False, "Failed to update password"
    
    def reset_password_request(self, email):
        """Request password reset (generates token)"""
        # This would typically generate a reset token and send email
        # For now, just return success
        return True, "Password reset instructions sent to email"
    
    def validate_username(self, username):
        """Validate username format and availability"""
        if not username or len(username) < 3:
            return False, "Username must be at least 3 characters long"
        
        if len(username) > 20:
            return False, "Username must be less than 20 characters"
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Username can only contain letters, numbers, and underscores"
        
        # Check if username is taken
        user = self.db.get_user_by_username(username)
        if user:
            return False, "Username already taken"
        
        return True, "Username is available"
    
    def get_user_info(self, user_id):
        """Get user information"""
        return self.db.get_user_by_id(user_id)
    
    def deactivate_account(self, user_id, password):
        """Deactivate user account"""
        # Get user
        user = self.db.get_user_by_id(user_id)
        
        if not user:
            return False, "User not found"
        
        # Verify password
        if not self.verify_password(password, user['password_hash']):
            return False, "Incorrect password"
        
        # Deactivate account
        success = self.db.deactivate_user(user_id)
        
        if success:
            return True, "Account deactivated successfully"
        else:
            return False, "Failed to deactivate account"
