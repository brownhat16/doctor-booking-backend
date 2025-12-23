"""
Session Manager for Lab Test Booking Agent
Manages user session state including cart, journey steps, and booking details.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

class SessionManager:
    """Manages user sessions for stateful cart and journey tracking"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def get_state(self, session_id: str) -> Dict[str, Any]:
        """
        Get current session state. Initializes new session if doesn't exist.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Session state dictionary
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = self._create_empty_state()
        
        return self.sessions[session_id]
    
    def update_state(self, session_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update session state with new values.
        
        Args:
            session_id: Unique session identifier
            updates: Dictionary of fields to update
            
        Returns:
            Updated session state
        """
        current_state = self.get_state(session_id)
        current_state.update(updates)
        current_state['last_updated'] = datetime.now().isoformat()
        
        return current_state
    
    def reset_state(self, session_id: str) -> Dict[str, Any]:
        """
        Reset session to empty state.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            New empty state
        """
        self.sessions[session_id] = self._create_empty_state()
        return self.sessions[session_id]
    
    def add_to_cart(self, session_id: str, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a test to the cart.
        
        Args:
            session_id: Unique session identifier
            item: Test item to add (test_id, test_name, price)
            
        Returns:
            Updated session state
        """
        state = self.get_state(session_id)
        
        # Check if item already in cart
        if any(i['test_id'] == item['test_id'] for i in state['cart']):
            return state  # Already in cart
        
        state['cart'].append(item)
        state['journey_step'] = 'cart'
        state['last_updated'] = datetime.now().isoformat()
        
        return state
    
    def remove_from_cart(self, session_id: str, test_id: str) -> Dict[str, Any]:
        """
        Remove a test from the cart.
        
        Args:
            session_id: Unique session identifier
            test_id: ID of test to remove
            
        Returns:
            Updated session state
        """
        state = self.get_state(session_id)
        state['cart'] = [item for item in state['cart'] if item['test_id'] != test_id]
        state['last_updated'] = datetime.now().isoformat()
        
        # If cart is empty, go back to discovery
        if not state['cart']:
            state['journey_step'] = 'discovery'
        
        return state
    
    def get_cart_total(self, session_id: str) -> int:
        """
        Calculate total price of items in cart.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Total price in rupees
        """
        state = self.get_state(session_id)
        return sum(item['price'] for item in state['cart'])
    
    def clear_cart(self, session_id: str) -> Dict[str, Any]:
        """
        Clear all items from cart.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Updated session state
        """
        state = self.get_state(session_id)
        state['cart'] = []
        state['journey_step'] = 'discovery'
        state['last_updated'] = datetime.now().isoformat()
        
        return state
    
    def _create_empty_state(self) -> Dict[str, Any]:
        """Create initial empty state for new session"""
        return {
            'journey_step': 'search',  # search | discovery | cart | availability | booking | post_booking
            'cart': [],  # List of {test_id, test_name, price}
            'filters': {},  # {max_price, home_collection, min_rating}
            'collection_method': None,  # home | lab
            'selected_slot': None,  # {slot_id, date, time, lab_name, lab_address}
            'booking_reference': None,  # booking_xxx after confirmation
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
