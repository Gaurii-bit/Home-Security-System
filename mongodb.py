"""
Database Module for Intelligent Security System
Handles all MongoDB operations including user management, embeddings, logs, and RBAC
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime
import os
from dotenv import load_dotenv
from typing import Dict, List, Optional, Any
import numpy as np

load_dotenv()

class SecurityDatabase:
    """MongoDB database handler for security system"""
    
    def __init__(self):
        """Initialize database connection"""
        self.uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        self.db_name = os.getenv('DATABASE_NAME', 'intelligent_security_db')
        self.client = None
        self.db = None
        self.connect()
        
    def connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.server_info()
            self.db = self.client[self.db_name]
            self._create_indexes()
            print(f"[OK] Connected to MongoDB: {self.db_name}")
        except Exception as e:
            print(f"[ERROR] MongoDB connection failed: {e}")
            print("  Running in standalone mode without database persistence")
            self.client = None
            self.db = None
    
    def _create_indexes(self):
        """Create indexes for better query performance"""
        if self.db is None:
            return
            
        # Users collection indexes
        self.db.users.create_index([("user_id", ASCENDING)], unique=True)
        self.db.users.create_index([("email", ASCENDING)], unique=True)
        
        # Embeddings collection indexes
        self.db.embeddings.create_index([("user_id", ASCENDING)])
        
        # Logs collection indexes
        self.db.logs.create_index([("timestamp", DESCENDING)])
        self.db.logs.create_index([("event_type", ASCENDING)])
        self.db.logs.create_index([("user_id", ASCENDING)])
        
        # RBAC collections indexes
        self.db.roles.create_index([("role_name", ASCENDING)], unique=True)
        self.db.permissions.create_index([("permission_name", ASCENDING)], unique=True)
        
    # ==================== USER MANAGEMENT ====================
    
    def add_user(self, user_data: Dict) -> bool:
        """Add a new user to the database"""
        if self.db is None:
            return False
            
        try:
            user_data['created_at'] = datetime.now()
            user_data['updated_at'] = datetime.now()
            self.db.users.insert_one(user_data)
            return True
        except Exception as e:
            print(f"Error adding user: {e}")
            return False
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Retrieve user by ID"""
        if self.db is None:
            return None
        return self.db.users.find_one({"user_id": user_id})
    
    def update_user(self, user_id: str, update_data: Dict) -> bool:
        """Update user information"""
        if self.db is None:
            return False
            
        try:
            update_data['updated_at'] = datetime.now()
            result = self.db.users.update_one(
                {"user_id": user_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating user: {e}")
            return False
    
    def get_all_users(self) -> List[Dict]:
        """Get all users"""
        if self.db is None:
            return []
        return list(self.db.users.find({}))
    
    # ==================== EMBEDDINGS MANAGEMENT ====================
    
    def store_embedding(self, user_id: str, embedding: np.ndarray, metadata: Dict = None) -> bool:
        """Store face embedding for a user"""
        if self.db is None:
            return False
            
        try:
            embedding_doc = {
                "user_id": user_id,
                "embedding": embedding.tolist(),
                "metadata": metadata or {},
                "created_at": datetime.now()
            }
            self.db.embeddings.insert_one(embedding_doc)
            return True
        except Exception as e:
            print(f"Error storing embedding: {e}")
            return False
    
    def get_embeddings(self, user_id: str = None) -> List[Dict]:
        """Get embeddings for a specific user or all embeddings"""
        if self.db is None:
            return []
            
        query = {"user_id": user_id} if user_id else {}
        embeddings = list(self.db.embeddings.find(query))
        
        # Convert embedding lists back to numpy arrays
        for emb in embeddings:
            emb['embedding'] = np.array(emb['embedding'])
        
        return embeddings
    
    # ==================== LOGGING ====================
    
    def log_event(self, event_type: str, data: Dict) -> bool:
        """Log a security event"""
        if self.db is None:
            return False
            
        try:
            log_entry = {
                "event_type": event_type,
                "timestamp": datetime.now(),
                "data": data
            }
            self.db.logs.insert_one(log_entry)
            return True
        except Exception as e:
            print(f"Error logging event: {e}")
            return False
    
    def get_logs(self, event_type: str = None, limit: int = 100) -> List[Dict]:
        """Retrieve logs with optional filtering"""
        if self.db is None:
            return []
            
        query = {"event_type": event_type} if event_type else {}
        return list(self.db.logs.find(query).sort("timestamp", DESCENDING).limit(limit))
    
    def get_user_logs(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get logs for a specific user"""
        if self.db is None:
            return []
        return list(self.db.logs.find({"data.user_id": user_id})
                   .sort("timestamp", DESCENDING).limit(limit))
    
    # ==================== RBAC MANAGEMENT ====================
    
    def create_role(self, role_name: str, permissions: List[str], description: str = "") -> bool:
        """Create a new role with permissions"""
        if self.db is None:
            return False
            
        try:
            role_doc = {
                "role_name": role_name,
                "permissions": permissions,
                "description": description,
                "created_at": datetime.now()
            }
            self.db.roles.insert_one(role_doc)
            return True
        except Exception as e:
            print(f"Error creating role: {e}")
            return False
    
    def get_role(self, role_name: str) -> Optional[Dict]:
        """Get role by name"""
        if self.db is None:
            return None
        return self.db.roles.find_one({"role_name": role_name})
    
    def assign_role_to_user(self, user_id: str, role_name: str) -> bool:
        """Assign a role to a user"""
        if self.db is None:
            return False
            
        return self.update_user(user_id, {"role": role_name})
    
    def create_permission(self, permission_name: str, description: str = "") -> bool:
        """Create a new permission"""
        if self.db is None:
            return False
            
        try:
            perm_doc = {
                "permission_name": permission_name,
                "description": description,
                "created_at": datetime.now()
            }
            self.db.permissions.insert_one(perm_doc)
            return True
        except Exception as e:
            print(f"Error creating permission: {e}")
            return False
    
    # ==================== BEHAVIORAL DATA ====================
    
    def store_behavioral_data(self, user_id: str, behavioral_score: float, 
                             anomaly_score: float, details: Dict) -> bool:
        """Store behavioral analysis data"""
        if self.db is None:
            return False
            
        try:
            behavior_doc = {
                "user_id": user_id,
                "behavioral_score": behavioral_score,
                "anomaly_score": anomaly_score,
                "details": details,
                "timestamp": datetime.now()
            }
            self.db.behavioral_data.insert_one(behavior_doc)
            return True
        except Exception as e:
            print(f"Error storing behavioral data: {e}")
            return False
    
    def get_behavioral_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get behavioral history for a user"""
        if self.db is None:
            return []
        return list(self.db.behavioral_data.find({"user_id": user_id})
                   .sort("timestamp", DESCENDING).limit(limit))
    
    # ==================== THREAT RECORDS ====================
    
    def store_threat_record(self, threat_data: Dict) -> bool:
        """Store threat assessment record"""
        if self.db is None:
            return False
            
        try:
            threat_data['timestamp'] = datetime.now()
            self.db.threats.insert_one(threat_data)
            return True
        except Exception as e:
            print(f"Error storing threat record: {e}")
            return False
    
    def get_threat_records(self, threat_level: str = None, limit: int = 50) -> List[Dict]:
        """Get threat records with optional filtering"""
        if self.db is None:
            return []
            
        query = {"threat_level": threat_level} if threat_level else {}
        return list(self.db.threats.find(query).sort("timestamp", DESCENDING).limit(limit))
    
    # ==================== UTILITY ====================
    
    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            print("[OK] Database connection closed")
    
    def clear_collection(self, collection_name: str) -> bool:
        """Clear a collection (for testing)"""
        if self.db is None:
            return False
            
        try:
            self.db[collection_name].delete_many({})
            return True
        except Exception as e:
            print(f"Error clearing collection: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        if self.db is None:
            return {"status": "disconnected"}
            
        try:
            stats = {
                "users": self.db.users.count_documents({}),
                "embeddings": self.db.embeddings.count_documents({}),
                "logs": self.db.logs.count_documents({}),
                "roles": self.db.roles.count_documents({}),
                "permissions": self.db.permissions.count_documents({}),
                "behavioral_records": self.db.behavioral_data.count_documents({}),
                "threat_records": self.db.threats.count_documents({})
            }
            return stats
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}