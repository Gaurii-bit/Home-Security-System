"""
Intelligent Home Security System
Main integration module combining all components
"""

import cv2
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

# Import all modules
from mongodb import SecurityDatabase
from face_recog import FaceRecognitionEngine
from behavioral_analysis import BehavioralAnalyzer
from threat_scoring import ThreatScoringEngine
from rbac import RBACEngine
from response_engine import ResponseEngine

load_dotenv()

class IntelligentSecuritySystem:
    """Main security system orchestrator"""
    
    def __init__(self):
        """Initialize all system components"""
        print("\n" + "="*70)
        print(" INTELLIGENT HOME SECURITY SYSTEM WITH RBAC")
        print(" Architecture with Adaptive Threat Response")
        print("="*70 + "\n")
        
        # Initialize database
        print("1. Initializing Database Connection...")
        self.db = SecurityDatabase()
        
        # Initialize face recognition
        print("2. Initializing Face Recognition Engine...")
        similarity_threshold = float(os.getenv('SIMILARITY_THRESHOLD', 0.7))
        self.face_engine = FaceRecognitionEngine(similarity_threshold=similarity_threshold)
        
        # Initialize behavioral analyzer
        print("3. Initializing Behavioral Analysis Module...")
        anomaly_threshold = float(os.getenv('ANOMALY_THRESHOLD', 0.5))
        self.behavioral_analyzer = BehavioralAnalyzer(anomaly_threshold=anomaly_threshold)
        
        # Initialize threat scoring
        print("4. Initializing Threat Scoring Engine...")
        w1 = float(os.getenv('WEIGHT_ANOMALY', 0.4))
        w2 = float(os.getenv('WEIGHT_BEHAVIORAL', 0.3))
        w3 = float(os.getenv('WEIGHT_RECOGNITION', 0.3))
        low_thresh = float(os.getenv('LOW_THREAT_THRESHOLD', 0.3))
        high_thresh = float(os.getenv('HIGH_THREAT_THRESHOLD', 0.7))
        
        self.threat_engine = ThreatScoringEngine(
            weight_anomaly=w1,
            weight_behavioral=w2,
            weight_recognition=w3,
            low_threshold=low_thresh,
            high_threshold=high_thresh
        )
        
        # Initialize RBAC
        print("5. Initializing RBAC Authorization Module...")
        self.rbac_engine = RBACEngine()
        
        # Initialize response engine
        print("6. Initializing Adaptive Response Engine...")
        self.response_engine = ResponseEngine()
        
        # Load known faces from database
        self._load_known_faces()
        
        print("\n[OK] System Initialization Complete\n")
    
    def _load_known_faces(self):
        """Load known face embeddings from database"""
        embeddings_data = self.db.get_embeddings()
        
        if embeddings_data:
            embeddings_dict = {}
            for emb_doc in embeddings_data:
                user_id = emb_doc['user_id']
                if user_id not in embeddings_dict:
                    embeddings_dict[user_id] = []
                embeddings_dict[user_id].append(emb_doc['embedding'])
            
            self.face_engine.load_embeddings(embeddings_dict)
        else:
            print("  No stored embeddings found in database")
    
    def register_user(self, user_id: str, name: str, email: str, 
                     role: str, face_image: np.ndarray) -> bool:
        """
        Register a new user with face enrollment
        
        Args:
            user_id: Unique user identifier
            name: User's full name
            email: User's email
            role: User's role (guest, resident, admin, security)
            face_image: Face image for enrollment
            
        Returns:
            True if successful
        """
        print(f"\nRegistering user: {name} ({user_id})")
        
        # Detect face
        face_locations = self.face_engine.detect_faces(face_image)
        
        if len(face_locations) == 0:
            print("[ERROR] No face detected in image")
            return False
        
        if len(face_locations) > 1:
            print("[ERROR] Multiple faces detected - please provide image with single face")
            return False
        
        # Extract embedding
        embedding = self.face_engine.extract_features(face_image, face_locations[0])
        
        if embedding is None:
            print("[ERROR] Failed to extract face features")
            return False
        
        # Create user in database
        user_data = {
            'user_id': user_id,
            'name': name,
            'email': email,
            'role': role,
            'status': 'active'
        }
        
        if not self.db.add_user(user_data):
            print("[ERROR] Failed to add user to database")
            return False
        
        # Store embedding
        if not self.db.store_embedding(user_id, embedding):
            print("[ERROR] Failed to store face embedding")
            return False
        
        # Add to face recognition engine
        self.face_engine.add_embedding(user_id, embedding)
        
        # Assign role in RBAC
        if not self.rbac_engine.assign_role(user_id, role):
            print("[ERROR] Failed to assign role")
            return False
        
        print(f"[OK] User {name} registered successfully with role '{role}'")
        return True
    
    def process_frame(self, frame: np.ndarray) -> Dict:
        """
        Process a single frame through the complete pipeline
        
        Pipeline:
        1. Video Acquisition & Frame Sampling
        2. Face Detection
        3. Preprocessing & Normalization
        4. Feature Extraction
        5. Identity Recognition
        6. Behavioral Analysis
        7. Anomaly Detection
        8. Threat Scoring
        9. RBAC Authorization
        10. Adaptive Response
        
        Args:
            frame: Input video frame
            
        Returns:
            Complete analysis results
        """
        timestamp = datetime.now()
        
        # Step 1-5: Face detection and recognition
        face_results = self.face_engine.process_frame(frame)
        
        if len(face_results) == 0:
            return {
                'timestamp': timestamp,
                'faces_detected': 0,
                'results': []
            }
        
        # Process each detected face
        all_results = []
        
        for face_result in face_results:
            user_id = face_result['user_id'] if face_result['user_id'] else 'unknown'
            is_authorized_face = face_result['is_authorized']
            similarity = face_result['similarity']
            location = face_result['location']
            
            # Step 6-7: Behavioral Analysis
            self.behavioral_analyzer.track_appearance(user_id, timestamp, location)
            behavioral_analysis = self.behavioral_analyzer.get_comprehensive_analysis(
                user_id, is_authorized_face
            )
            
            behavioral_score = behavioral_analysis['behavioral_score']
            anomaly_score = behavioral_analysis['anomaly_score']
            
            # Step 8: Threat Scoring
            threat_assessment = self.threat_engine.assess_threat(
                anomaly_score=anomaly_score,
                behavioral_score=behavioral_score,
                is_authorized=is_authorized_face,
                similarity=similarity
            )
            
            # Step 9: RBAC Authorization
            rbac_result = self.rbac_engine.authorize_access(user_id, 'access:enter')
            
            # Step 10: Adaptive Response
            response = self.response_engine.determine_response(
                threat_level=threat_assessment['threat_level'],
                is_authorized=rbac_result['authorized'],
                user_id=user_id
            )
            
            # Combine all results
            complete_result = {
                'user_id': user_id,
                'timestamp': timestamp,
                'face_recognition': {
                    'is_recognized': is_authorized_face,
                    'similarity': similarity,
                    'location': location
                },
                'behavioral_analysis': behavioral_analysis,
                'threat_assessment': threat_assessment,
                'rbac_authorization': rbac_result,
                'response': response
            }
            
            all_results.append(complete_result)
            
            # Log to database
            self._log_event(complete_result)
        
        return {
            'timestamp': timestamp,
            'faces_detected': len(face_results),
            'results': all_results,
            'annotated_frame': self.face_engine.draw_results(frame, face_results)
        }
    
    def _log_event(self, result: Dict):
        """Log security event to database"""
        log_data = {
            'user_id': result['user_id'],
            'threat_level': result['threat_assessment']['threat_level'],
            'is_authorized': result['rbac_authorization']['authorized'],
            'similarity': result['face_recognition']['similarity'],
            'behavioral_score': result['behavioral_analysis']['behavioral_score'],
            'anomaly_score': result['behavioral_analysis']['anomaly_score'],
            'threat_score': result['threat_assessment']['weighted_threat_score']
        }
        
        self.db.log_event('face_detection', log_data)
        self.db.store_threat_record(result['threat_assessment'])
        self.db.store_behavioral_data(
            result['user_id'],
            result['behavioral_analysis']['behavioral_score'],
            result['behavioral_analysis']['anomaly_score'],
            result['behavioral_analysis']
        )
    
    def get_system_status(self) -> Dict:
        """Get current system status and statistics"""
        db_stats = self.db.get_statistics()
        response_summary = self.response_engine.get_response_summary(60)
        
        return {
            'database': db_stats,
            'recent_responses': response_summary,
            'registered_users': len(self.face_engine.known_embeddings),
            'roles': list(self.rbac_engine.roles.keys()),
            'timestamp': datetime.now()
        }
    
    def display_result(self, result: Dict):
        """Display comprehensive result in console"""
        print("\n" + "="*80)
        print(f" SECURITY ANALYSIS - {result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        for i, face_result in enumerate(result['results'], 1):
            print(f"\n--- Face #{i} ---")
            print(f"User ID: {face_result['user_id']}")
            print(f"Recognized: {face_result['face_recognition']['is_recognized']}")
            print(f"Similarity: {face_result['face_recognition']['similarity']:.3f}")
            
            print(f"\nBehavioral Score: {face_result['behavioral_analysis']['behavioral_score']:.3f}")
            print(f"Anomaly Score: {face_result['behavioral_analysis']['anomaly_score']:.3f}")
            
            print(f"\nThreat Assessment:")
            print(f"  Weighted Score: {face_result['threat_assessment']['weighted_threat_score']:.3f}")
            print(f"  Level: {face_result['threat_assessment']['threat_level']}")
            
            print(f"\nRBAC Authorization:")
            print(f"  Role: {face_result['rbac_authorization'].get('role', 'None')}")
            print(f"  Authorized: {face_result['rbac_authorization']['authorized']}")
            print(f"  Decision: {'ACCESS GRANTED' if face_result['rbac_authorization']['authorized'] else 'ACCESS DENIED'}")
            
            print(f"\nResponse Actions:")
            for action in face_result['response']['actions']:
                print(f"  • {action}")
        
        print("\n" + "="*80 + "\n")
    
    def cleanup(self):
        """Cleanup and close connections"""
        self.db.close()
        print("[OK] System shutdown complete")