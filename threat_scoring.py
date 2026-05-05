"""
Adaptive Threat Scoring and Classification Module
Implements weighted fusion of anomaly, behavioral, and recognition scores
"""

import numpy as np
from typing import Dict, Tuple
from datetime import datetime

class ThreatScoringEngine:
    """Adaptive threat scoring with weighted fusion"""
    
    def __init__(self, 
                 weight_anomaly: float = 0.4,
                 weight_behavioral: float = 0.3,
                 weight_recognition: float = 0.3,
                 low_threshold: float = 0.3,
                 high_threshold: float = 0.7):
        """
        Initialize threat scoring engine
        
        Args:
            weight_anomaly: Weight for anomaly score
            weight_behavioral: Weight for behavioral score
            weight_recognition: Weight for recognition score
            low_threshold: Threshold for low/medium threat
            high_threshold: Threshold for medium/high threat
        """
        # Ensure weights sum to 1
        total = weight_anomaly + weight_behavioral + weight_recognition
        self.w1 = weight_anomaly / total
        self.w2 = weight_behavioral / total
        self.w3 = weight_recognition / total
        
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold
        
    def compute_recognition_score(self, is_authorized: bool, similarity: float) -> float:
        """
        Compute recognition-based threat score
        
        Args:
            is_authorized: Whether face is recognized
            similarity: Face similarity score
            
        Returns:
            Recognition threat score (0-1, higher is more threatening)
        """
        if is_authorized:
            # Authorized user - low threat, but consider similarity confidence
            return (1.0 - similarity) * 0.2
        else:
            # Unauthorized user - threat based on how unknown they are
            return 0.8 + (1.0 - similarity) * 0.2
    
    def compute_weighted_threat_score(self, 
                                     anomaly_score: float,
                                     behavioral_score: float,
                                     recognition_score: float) -> float:
        """
        Compute weighted fusion threat score
        T(x) = w1*A(x) + w2*B(x) + w3*R(x)
        
        Args:
            anomaly_score: Anomaly detection score (0-1)
            behavioral_score: Behavioral analysis score (0-1, inverted for threat)
            recognition_score: Recognition-based score (0-1)
            
        Returns:
            Weighted threat score (0-1)
        """
        # Behavioral score is inverted (high behavior score = normal = low threat)
        behavioral_threat = 1.0 - behavioral_score
        
        # Weighted fusion
        threat_score = (self.w1 * anomaly_score + 
                       self.w2 * behavioral_threat + 
                       self.w3 * recognition_score)
        
        return threat_score
    
    def compute_simple_average_threat_score(self,
                                           anomaly_score: float,
                                           behavioral_score: float,
                                           recognition_score: float) -> float:
        """
        Compute simple average threat score
        T(x) = (A(x) + B(x) + R(x)) / 3
        
        Args:
            anomaly_score: Anomaly detection score
            behavioral_score: Behavioral analysis score (inverted)
            recognition_score: Recognition-based score
            
        Returns:
            Average threat score (0-1)
        """
        behavioral_threat = 1.0 - behavioral_score
        return (anomaly_score + behavioral_threat + recognition_score) / 3.0
    
    def classify_threat_level(self, threat_score: float) -> str:
        """
        Classify threat into Low, Medium, or High
        
        Args:
            threat_score: Computed threat score
            
        Returns:
            Threat level: 'LOW', 'MEDIUM', or 'HIGH'
        """
        if threat_score < self.low_threshold:
            return 'LOW'
        elif threat_score < self.high_threshold:
            return 'MEDIUM'
        else:
            return 'HIGH'
    
    def assess_threat(self,
                     anomaly_score: float,
                     behavioral_score: float,
                     is_authorized: bool,
                     similarity: float) -> Dict:
        """
        Complete threat assessment
        
        Args:
            anomaly_score: Anomaly score from behavioral analyzer
            behavioral_score: Behavioral score
            is_authorized: Whether user is recognized
            similarity: Face similarity score
            
        Returns:
            Complete threat assessment dictionary
        """
        # Compute recognition score
        recognition_score = self.compute_recognition_score(is_authorized, similarity)
        
        # Compute threat scores (both methods)
        weighted_threat = self.compute_weighted_threat_score(
            anomaly_score, behavioral_score, recognition_score
        )
        
        simple_threat = self.compute_simple_average_threat_score(
            anomaly_score, behavioral_score, recognition_score
        )
        
        # Use weighted score for classification
        threat_level = self.classify_threat_level(weighted_threat)
        
        return {
            'anomaly_score': anomaly_score,
            'behavioral_score': behavioral_score,
            'recognition_score': recognition_score,
            'weighted_threat_score': weighted_threat,
            'simple_threat_score': simple_threat,
            'threat_level': threat_level,
            'is_authorized': is_authorized,
            'similarity': similarity,
            'weights': {
                'w1_anomaly': self.w1,
                'w2_behavioral': self.w2,
                'w3_recognition': self.w3
            },
            'timestamp': datetime.now()
        }
    
    def get_threat_description(self, threat_level: str) -> Dict:
        """
        Get description and recommended actions for threat level
        
        Args:
            threat_level: Threat classification
            
        Returns:
            Dictionary with description and actions
        """
        descriptions = {
            'LOW': {
                'description': 'Low security risk - Authorized user or normal behavior',
                'actions': [
                    'Log activity',
                    'Continue monitoring',
                    'No immediate action'
                ],
                'alert_type': 'info',
                'color': 'green'
            },
            'MEDIUM': {
                'description': 'Medium security risk - Unusual behavior or unrecognized user',
                'actions': [
                    'Send alert to user/admin',
                    'Increase monitoring frequency',
                    'Record event for analysis'
                ],
                'alert_type': 'warning',
                'color': 'yellow'
            },
            'HIGH': {
                'description': 'High security risk - Potential security breach',
                'actions': [
                    'Immediate alert to admin',
                    'Activate alarm/siren',
                    'Lock/restrict access',
                    'Escalate to security personnel',
                    'Capture and store evidence'
                ],
                'alert_type': 'critical',
                'color': 'red'
            }
        }
        
        return descriptions.get(threat_level, descriptions['MEDIUM'])