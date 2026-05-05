"""
Behavioral Analysis and Anomaly Detection Module
Analyzes patterns and detects anomalies in user behavior
"""

import numpy as np
from typing import Dict, List, Tuple
from collections import deque
from datetime import datetime, timedelta

class BehavioralAnalyzer:
    """Analyzes user behavior patterns and detects anomalies"""
    
    def __init__(self, window_size: int = 10, anomaly_threshold: float = 0.5):
        """
        Initialize behavioral analyzer
        
        Args:
            window_size: Number of recent events to consider
            anomaly_threshold: Threshold for anomaly detection
        """
        self.window_size = window_size
        self.anomaly_threshold = anomaly_threshold
        self.behavioral_history = {}  # {user_id: deque of events}
        
    def track_appearance(self, user_id: str, timestamp: datetime, location: Tuple[int, int, int, int]):
        """
        Track user appearance
        
        Args:
            user_id: User identifier
            timestamp: Time of appearance
            location: Face bounding box location
        """
        if user_id not in self.behavioral_history:
            self.behavioral_history[user_id] = deque(maxlen=self.window_size)
        
        event = {
            'type': 'appearance',
            'timestamp': timestamp,
            'location': location,
            'center': self._get_center(location)
        }
        
        self.behavioral_history[user_id].append(event)
    
    def _get_center(self, location: Tuple[int, int, int, int]) -> Tuple[int, int]:
        """Get center point of bounding box"""
        top, right, bottom, left = location
        center_x = (left + right) // 2
        center_y = (top + bottom) // 2
        return (center_x, center_y)
    
    def analyze_duration_of_stay(self, user_id: str) -> Dict:
        """
        Analyze how long user has been present
        
        Args:
            user_id: User identifier
            
        Returns:
            Duration statistics
        """
        if user_id not in self.behavioral_history or len(self.behavioral_history[user_id]) == 0:
            return {'duration_seconds': 0, 'status': 'new'}
        
        events = list(self.behavioral_history[user_id])
        first_seen = events[0]['timestamp']
        last_seen = events[-1]['timestamp']
        
        duration = (last_seen - first_seen).total_seconds()
        
        # Classify duration
        if duration < 30:
            status = 'brief'
        elif duration < 300:  # 5 minutes
            status = 'normal'
        elif duration < 1800:  # 30 minutes
            status = 'extended'
        else:
            status = 'prolonged'
        
        return {
            'duration_seconds': duration,
            'status': status,
            'first_seen': first_seen,
            'last_seen': last_seen,
            'num_appearances': len(events)
        }
    
    def analyze_repeated_attempts(self, user_id: str = None) -> Dict:
        """
        Analyze repeated access attempts (especially for unknown users)
        
        Args:
            user_id: User identifier (None for unknown)
            
        Returns:
            Attempt statistics
        """
        key = user_id if user_id else 'unknown'
        
        if key not in self.behavioral_history:
            return {'num_attempts': 0, 'is_suspicious': False}
        
        events = list(self.behavioral_history[key])
        num_attempts = len(events)
        
        # Calculate time span
        if num_attempts > 1:
            time_span = (events[-1]['timestamp'] - events[0]['timestamp']).total_seconds()
            attempts_per_minute = num_attempts / (time_span / 60) if time_span > 0 else num_attempts
        else:
            attempts_per_minute = 0
        
        # Suspicious if many attempts in short time
        is_suspicious = num_attempts > 5 and attempts_per_minute > 2
        
        return {
            'num_attempts': num_attempts,
            'attempts_per_minute': attempts_per_minute,
            'is_suspicious': is_suspicious
        }
    
    def analyze_motion_intensity(self, user_id: str) -> Dict:
        """
        Analyze motion patterns based on position changes
        
        Args:
            user_id: User identifier
            
        Returns:
            Motion statistics
        """
        if user_id not in self.behavioral_history or len(self.behavioral_history[user_id]) < 2:
            return {'motion_intensity': 0.0, 'status': 'static'}
        
        events = list(self.behavioral_history[user_id])
        
        # Calculate movement between consecutive appearances
        movements = []
        for i in range(1, len(events)):
            prev_center = events[i-1]['center']
            curr_center = events[i]['center']
            
            # Euclidean distance
            distance = np.sqrt((curr_center[0] - prev_center[0])**2 + 
                             (curr_center[1] - prev_center[1])**2)
            movements.append(distance)
        
        avg_movement = np.mean(movements) if movements else 0
        
        # Classify motion intensity
        if avg_movement < 10:
            status = 'static'
        elif avg_movement < 50:
            status = 'low'
        elif avg_movement < 150:
            status = 'moderate'
        else:
            status = 'high'
        
        return {
            'motion_intensity': float(avg_movement),
            'status': status,
            'total_displacement': sum(movements)
        }
    
    def analyze_time_patterns(self, user_id: str) -> Dict:
        """
        Analyze temporal patterns of appearances
        
        Args:
            user_id: User identifier
            
        Returns:
            Time pattern statistics
        """
        if user_id not in self.behavioral_history or len(self.behavioral_history[user_id]) < 2:
            return {'regularity': 'insufficient_data'}
        
        events = list(self.behavioral_history[user_id])
        
        # Calculate time intervals between appearances
        intervals = []
        for i in range(1, len(events)):
            interval = (events[i]['timestamp'] - events[i-1]['timestamp']).total_seconds()
            intervals.append(interval)
        
        avg_interval = np.mean(intervals)
        std_interval = np.std(intervals)
        
        # Regularity based on standard deviation
        if std_interval < avg_interval * 0.3:
            regularity = 'regular'
        elif std_interval < avg_interval * 0.7:
            regularity = 'semi_regular'
        else:
            regularity = 'irregular'
        
        return {
            'avg_interval_seconds': float(avg_interval),
            'std_interval': float(std_interval),
            'regularity': regularity
        }
    
    def compute_behavioral_score(self, user_id: str) -> float:
        """
        Compute overall behavioral score (normal behavior = high score)
        
        Args:
            user_id: User identifier
            
        Returns:
            Behavioral score (0-1, higher is more normal)
        """
        duration_info = self.analyze_duration_of_stay(user_id)
        attempts_info = self.analyze_repeated_attempts(user_id)
        motion_info = self.analyze_motion_intensity(user_id)
        
        # Initialize score
        score = 1.0
        
        # Penalize prolonged stay
        if duration_info['status'] == 'prolonged':
            score -= 0.3
        elif duration_info['status'] == 'extended':
            score -= 0.1
        
        # Penalize suspicious repeated attempts
        if attempts_info['is_suspicious']:
            score -= 0.4
        
        # Penalize high motion intensity
        if motion_info['status'] == 'high':
            score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def compute_anomaly_score(self, user_id: str, is_authorized: bool) -> float:
        """
        Compute anomaly score based on behavioral patterns
        
        Args:
            user_id: User identifier
            is_authorized: Whether user is recognized
            
        Returns:
            Anomaly score (0-1, higher is more anomalous)
        """
        # Unknown users get higher base anomaly
        if not is_authorized:
            base_score = 0.6
        else:
            base_score = 0.1
        
        attempts_info = self.analyze_repeated_attempts(user_id)
        duration_info = self.analyze_duration_of_stay(user_id)
        
        # Increase score for suspicious patterns
        if attempts_info['is_suspicious']:
            base_score += 0.3
        
        if duration_info['status'] == 'prolonged':
            base_score += 0.2
        
        # Normalize to total number of unauthorized appearances
        if not is_authorized:
            unauthorized_count = attempts_info['num_attempts']
            if unauthorized_count > 10:
                base_score += 0.1
        
        return min(1.0, base_score)
    
    def get_comprehensive_analysis(self, user_id: str, is_authorized: bool) -> Dict:
        """
        Get complete behavioral analysis
        
        Args:
            user_id: User identifier
            is_authorized: Whether user is recognized
            
        Returns:
            Complete behavioral analysis dictionary
        """
        return {
            'duration': self.analyze_duration_of_stay(user_id),
            'attempts': self.analyze_repeated_attempts(user_id),
            'motion': self.analyze_motion_intensity(user_id),
            'time_patterns': self.analyze_time_patterns(user_id),
            'behavioral_score': self.compute_behavioral_score(user_id),
            'anomaly_score': self.compute_anomaly_score(user_id, is_authorized)
        }
    
    def clear_history(self, user_id: str = None):
        """Clear behavioral history"""
        if user_id:
            if user_id in self.behavioral_history:
                del self.behavioral_history[user_id]
        else:
            self.behavioral_history.clear()