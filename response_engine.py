"""
Adaptive Response Engine
Determines and executes appropriate responses based on threat level
"""

from typing import Dict, List
from datetime import datetime
import json

class ResponseEngine:
    """Adaptive response based on threat level and access decision"""
    
    def __init__(self):
        """Initialize response engine"""
        self.response_history = []
        
    def determine_response(self, threat_level: str, is_authorized: bool, 
                          user_id: str = None) -> Dict:
        """
        Determine appropriate response based on threat and authorization
        
        Args:
            threat_level: 'LOW', 'MEDIUM', or 'HIGH'
            is_authorized: Whether user is authorized (RBAC result)
            user_id: User identifier
            
        Returns:
            Response action dictionary
        """
        response = {
            'threat_level': threat_level,
            'is_authorized': is_authorized,
            'user_id': user_id,
            'timestamp': datetime.now(),
            'actions': [],
            'alerts': [],
            'system_changes': []
        }
        
        # Response matrix based on threat level
        if threat_level == 'LOW':
            response['actions'] = self._low_threat_response(is_authorized)
            response['alert_level'] = 'info'
            response['priority'] = 1
            
        elif threat_level == 'MEDIUM':
            response['actions'] = self._medium_threat_response(is_authorized)
            response['alert_level'] = 'warning'
            response['priority'] = 2
            
        elif threat_level == 'HIGH':
            response['actions'] = self._high_threat_response(is_authorized)
            response['alert_level'] = 'critical'
            response['priority'] = 3
        
        # Add authorization-specific actions
        if is_authorized:
            response['access_granted'] = True
            response['system_changes'].append('Grant access')
        else:
            response['access_granted'] = False
            response['system_changes'].append('Deny access')
        
        # Log response
        self.response_history.append(response)
        
        return response
    
    def _low_threat_response(self, is_authorized: bool) -> List[str]:
        """Actions for low threat scenarios"""
        actions = [
            'Log activity',
            'Continue monitoring',
            'No immediate action required'
        ]
        
        if is_authorized:
            actions.append('Welcome authorized user')
        else:
            actions.append('Record unknown visitor')
        
        return actions
    
    def _medium_threat_response(self, is_authorized: bool) -> List[str]:
        """Actions for medium threat scenarios"""
        actions = [
            'Send alert to user/administrator',
            'Increase monitoring frequency',
            'Record detailed event log',
            'Capture additional photos/video'
        ]
        
        if not is_authorized:
            actions.extend([
                'Request identification',
                'Send notification to primary user'
            ])
        else:
            actions.append('Verify unusual behavior with user')
        
        return actions
    
    def _high_threat_response(self, is_authorized: bool) -> List[str]:
        """Actions for high threat scenarios"""
        actions = [
            'IMMEDIATE ALERT to administrator',
            'Activate security alarm/siren',
            'Lock/restrict all access points',
            'Escalate to security personnel',
            'Capture and store high-resolution evidence',
            'Initiate emergency protocol'
        ]
        
        if not is_authorized:
            actions.extend([
                'Alert law enforcement (if configured)',
                'Trigger external alarm',
                'Send emergency notifications to all users'
            ])
        else:
            actions.append('Verify account security - possible compromise')
        
        return actions
    
    def execute_response(self, response: Dict) -> Dict:
        """
        Simulate execution of response actions
        
        Args:
            response: Response dictionary from determine_response()
            
        Returns:
            Execution result
        """
        execution_log = {
            'timestamp': datetime.now(),
            'threat_level': response['threat_level'],
            'executed_actions': [],
            'alerts_sent': [],
            'errors': []
        }
        
        # Execute each action
        for action in response['actions']:
            try:
                result = self._execute_action(action, response)
                execution_log['executed_actions'].append({
                    'action': action,
                    'status': 'success',
                    'result': result
                })
            except Exception as e:
                execution_log['errors'].append({
                    'action': action,
                    'error': str(e)
                })
        
        # Send alerts based on alert level
        alert = self._generate_alert(response)
        execution_log['alerts_sent'].append(alert)
        
        return execution_log
    
    def _execute_action(self, action: str, response: Dict) -> str:
        """
        Execute individual action (simulated)
        
        Args:
            action: Action description
            response: Full response context
            
        Returns:
            Execution result message
        """
        # This is a simulation - in real implementation, 
        # these would trigger actual hardware/software systems
        
        action_lower = action.lower()
        
        if 'log' in action_lower:
            return f"Event logged at {datetime.now()}"
        
        elif 'alert' in action_lower or 'notification' in action_lower:
            return f"Alert sent to administrators: {response['threat_level']} threat detected"
        
        elif 'alarm' in action_lower or 'siren' in action_lower:
            return "Security alarm activated"
        
        elif 'lock' in action_lower or 'restrict' in action_lower:
            return "Access points secured"
        
        elif 'capture' in action_lower or 'record' in action_lower:
            return "High-resolution evidence captured"
        
        elif 'monitor' in action_lower:
            return "Monitoring frequency increased"
        
        else:
            return f"Action executed: {action}"
    
    def _generate_alert(self, response: Dict) -> Dict:
        """
        Generate alert message based on response
        
        Args:
            response: Response dictionary
            
        Returns:
            Alert dictionary
        """
        alert = {
            'timestamp': datetime.now(),
            'level': response['alert_level'],
            'threat_level': response['threat_level'],
            'message': '',
            'user_id': response.get('user_id', 'Unknown'),
            'is_authorized': response['is_authorized']
        }
        
        # Generate appropriate message
        if response['threat_level'] == 'LOW':
            if response['is_authorized']:
                alert['message'] = f"Authorized user {alert['user_id']} detected - Normal activity"
            else:
                alert['message'] = f"Unknown person detected - Low threat"
        
        elif response['threat_level'] == 'MEDIUM':
            if response['is_authorized']:
                alert['message'] = f"⚠️ Unusual behavior detected for user {alert['user_id']}"
            else:
                alert['message'] = f"⚠️ Unrecognized person with suspicious behavior detected"
        
        elif response['threat_level'] == 'HIGH':
            if response['is_authorized']:
                alert['message'] = f"🚨 CRITICAL: Highly unusual activity for user {alert['user_id']} - Possible account compromise"
            else:
                alert['message'] = f"🚨 CRITICAL: High-threat intruder detected - Emergency response activated"
        
        return alert
    
    def get_response_summary(self, time_window_minutes: int = 60) -> Dict:
        """
        Get summary of recent responses
        
        Args:
            time_window_minutes: Time window for summary
            
        Returns:
            Response summary statistics
        """
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        recent_responses = [r for r in self.response_history 
                          if r['timestamp'] > cutoff_time]
        
        summary = {
            'total_responses': len(recent_responses),
            'low_threat': sum(1 for r in recent_responses if r['threat_level'] == 'LOW'),
            'medium_threat': sum(1 for r in recent_responses if r['threat_level'] == 'MEDIUM'),
            'high_threat': sum(1 for r in recent_responses if r['threat_level'] == 'HIGH'),
            'authorized_access': sum(1 for r in recent_responses if r['is_authorized']),
            'unauthorized_access': sum(1 for r in recent_responses if not r['is_authorized']),
            'time_window_minutes': time_window_minutes
        }
        
        return summary
    
    def format_response_for_display(self, response: Dict) -> str:
        """
        Format response for console display
        
        Args:
            response: Response dictionary
            
        Returns:
            Formatted string
        """
        lines = []
        lines.append(f"\n{'='*60}")
        lines.append(f"RESPONSE DETERMINATION - {response['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"{'='*60}")
        lines.append(f"Threat Level: {response['threat_level']}")
        lines.append(f"Authorization Status: {'AUTHORIZED' if response['is_authorized'] else 'UNAUTHORIZED'}")
        lines.append(f"User ID: {response.get('user_id', 'Unknown')}")
        lines.append(f"Access Decision: {'GRANTED' if response.get('access_granted') else 'DENIED'}")
        lines.append(f"\nActions to Execute:")
        for i, action in enumerate(response['actions'], 1):
            lines.append(f"  {i}. {action}")
        lines.append(f"{'='*60}\n")
        
        return '\n'.join(lines)
    