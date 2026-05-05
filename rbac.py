"""
RBAC (Role-Based Access Control) Module
Implements user-role assignment and permission-based access control
"""

from typing import Dict, List, Set, Optional
from datetime import datetime

class RBACEngine:
    """Role-Based Access Control Engine"""
    
    def __init__(self):
        """Initialize RBAC engine"""
        self.roles = {}  # {role_name: {'permissions': set(), 'description': str}}
        self.user_roles = {}  # {user_id: role_name}
        self.permissions = {}  # {permission_name: description}
        
        # Initialize default roles and permissions
        self._initialize_default_rbac()
    
    def _initialize_default_rbac(self):
        """Set up default roles and permissions"""
        # Define permissions
        default_permissions = {
            'access:enter': 'Permission to enter premises',
            'access:restricted_area': 'Permission to access restricted areas',
            'access:admin_panel': 'Permission to access admin panel',
            'access:security_logs': 'Permission to view security logs',
            'modify:users': 'Permission to modify user accounts',
            'modify:roles': 'Permission to modify roles and permissions',
            'view:cameras': 'Permission to view camera feeds',
            'control:doors': 'Permission to control door locks',
            'control:alarms': 'Permission to control alarm systems'
        }
        
        for perm_name, description in default_permissions.items():
            self.create_permission(perm_name, description)
        
        # Define roles
        self.create_role('guest', 
                        ['access:enter'],
                        'Guest user with basic access')
        
        self.create_role('resident',
                        ['access:enter', 'view:cameras'],
                        'Resident with home access and camera viewing')
        
        self.create_role('admin',
                        ['access:enter', 'access:restricted_area', 
                         'access:admin_panel', 'access:security_logs',
                         'view:cameras', 'control:doors', 'control:alarms',
                         'modify:users'],
                        'Administrator with full access')
        
        self.create_role('security',
                        ['access:enter', 'access:security_logs',
                         'view:cameras', 'control:doors', 'control:alarms'],
                        'Security personnel')
    
    def create_permission(self, permission_name: str, description: str = ""):
        """
        Create a new permission
        
        Args:
            permission_name: Unique permission identifier
            description: Permission description
        """
        self.permissions[permission_name] = {
            'description': description,
            'created_at': datetime.now()
        }
    
    def create_role(self, role_name: str, permissions: List[str], description: str = ""):
        """
        Create a new role with associated permissions
        
        Args:
            role_name: Unique role identifier
            permissions: List of permission names
            description: Role description
        """
        # Validate permissions exist
        valid_permissions = set()
        for perm in permissions:
            if perm in self.permissions:
                valid_permissions.add(perm)
            else:
                print(f"Warning: Permission '{perm}' does not exist")
        
        self.roles[role_name] = {
            'permissions': valid_permissions,
            'description': description,
            'created_at': datetime.now()
        }
    
    def assign_role(self, user_id: str, role_name: str) -> bool:
        """
        Assign a role to a user
        
        Args:
            user_id: User identifier
            role_name: Role to assign
            
        Returns:
            True if successful, False otherwise
        """
        if role_name not in self.roles:
            print(f"Error: Role '{role_name}' does not exist")
            return False
        
        self.user_roles[user_id] = role_name
        return True
    
    def get_user_role(self, user_id: str) -> Optional[str]:
        """
        Get role assigned to a user
        
        Args:
            user_id: User identifier
            
        Returns:
            Role name or None if not assigned
        """
        return self.user_roles.get(user_id)
    
    def get_user_permissions(self, user_id: str) -> Set[str]:
        """
        Get all permissions for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            Set of permission names
        """
        role_name = self.get_user_role(user_id)
        if role_name and role_name in self.roles:
            return self.roles[role_name]['permissions'].copy()
        return set()
    
    def check_permission(self, user_id: str, permission: str) -> bool:
        """
        Check if user has a specific permission
        
        Args:
            user_id: User identifier
            permission: Permission to check
            
        Returns:
            True if user has permission, False otherwise
        """
        user_permissions = self.get_user_permissions(user_id)
        return permission in user_permissions
    
    def authorize_access(self, user_id: str, required_permission: str = 'access:enter') -> Dict:
        """
        Complete authorization check with detailed result
        
        Args:
            user_id: User identifier
            required_permission: Permission required for access
            
        Returns:
            Authorization result dictionary
        """
        role = self.get_user_role(user_id)
        
        if not role:
            return {
                'authorized': False,
                'user_id': user_id,
                'role': None,
                'reason': 'No role assigned',
                'access_decision': 0,
                'timestamp': datetime.now()
            }
        
        has_permission = self.check_permission(user_id, required_permission)
        
        return {
            'authorized': has_permission,
            'user_id': user_id,
            'role': role,
            'required_permission': required_permission,
            'all_permissions': list(self.get_user_permissions(user_id)),
            'reason': 'Access granted' if has_permission else 'Insufficient permissions',
            'access_decision': 1 if has_permission else 0,
            'timestamp': datetime.now()
        }
    
    def add_permission_to_role(self, role_name: str, permission: str) -> bool:
        """
        Add a permission to an existing role
        
        Args:
            role_name: Role to modify
            permission: Permission to add
            
        Returns:
            True if successful
        """
        if role_name not in self.roles:
            print(f"Error: Role '{role_name}' does not exist")
            return False
        
        if permission not in self.permissions:
            print(f"Error: Permission '{permission}' does not exist")
            return False
        
        self.roles[role_name]['permissions'].add(permission)
        return True
    
    def remove_permission_from_role(self, role_name: str, permission: str) -> bool:
        """
        Remove a permission from a role
        
        Args:
            role_name: Role to modify
            permission: Permission to remove
            
        Returns:
            True if successful
        """
        if role_name not in self.roles:
            return False
        
        if permission in self.roles[role_name]['permissions']:
            self.roles[role_name]['permissions'].remove(permission)
            return True
        return False
    
    def get_all_roles(self) -> Dict:
        """Get all roles with their permissions"""
        return {
            role_name: {
                'permissions': list(role_data['permissions']),
                'description': role_data['description']
            }
            for role_name, role_data in self.roles.items()
        }
    
    def get_all_permissions(self) -> Dict:
        """Get all available permissions"""
        return self.permissions.copy()
    
    def get_role_details(self, role_name: str) -> Optional[Dict]:
        """
        Get detailed information about a role
        
        Args:
            role_name: Role to query
            
        Returns:
            Role details or None
        """
        if role_name in self.roles:
            return {
                'role_name': role_name,
                'permissions': list(self.roles[role_name]['permissions']),
                'description': self.roles[role_name]['description'],
                'permission_count': len(self.roles[role_name]['permissions'])
            }
        return None