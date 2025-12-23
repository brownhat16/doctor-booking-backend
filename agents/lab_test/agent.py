from typing import List, Dict, Optional
from .database import LabTestDatabase
from .models import LabTest, LabPackage, LabSlot, CartItem, LabBooking, LabOffering
from .session_manager import SessionManager
import random
from datetime import datetime

class LabTestAgent:
    def __init__(self):
        self.db = LabTestDatabase()
        self.session_manager = SessionManager()
    
    def search_tests(self, query: str, session_id: str, filters: Optional[Dict] = None) -> List[Dict]:
        """Search for lab tests with multi-lab offerings"""
        results = self.db.search_tests(query, filters)
        
        # Update session journey
        self.session_manager.update_state(session_id, {'journey_step': 'discovery'})
        
        # Format for frontend with all lab offerings
        formatted = []
        for test in results[:10]:  # Top 10 results
            # Format lab offerings for each test
            labs_data = []
            for lab in test.labs_offering:
                labs_data.append({
                    'lab_id': lab.lab_id,
                    'lab_name': lab.lab_name,
                    'lab_rating': lab.lab_rating,
                    'lab_location': lab.lab_location,
                    'price': lab.price,
                    'home_collection_available': lab.home_collection_available,
                    'home_collection_fee': lab.home_collection_fee,
                    'turnaround_time': lab.turnaround_time,
                    'accreditation': lab.accreditation
                })
            
            formatted.append({
                'id': test.id,
                'name': test.name,
                'category': test.category,
                'sample_type': test.sample_type,
                'fasting_required': test.fasting_required,
                'preparation_instructions': test.preparation_instructions,
                'parameters_count': test.parameters_count,
                'rating': test.rating,
                'booking_count': test.booking_count,
                'labs_offering': labs_data  # All lab options for this test
            })
        
        return formatted
    
    def search_by_lab(self, lab_name: str) -> List[Dict]:
        """Search all tests available at a specific lab"""
        all_tests = []
        for test in self.db.tests:
            for lab in test.labs_offering:
                if lab_name.lower() in lab.lab_name.lower():
                    all_tests.append({
                        'test_id': test.id,
                        'test_name': test.name,
                        'category': test.category,
                        'lab_name': lab.lab_name,
                        'price': lab.price,
                        'turnaround_time': lab.turnaround_time,
                        'home_collection': lab.home_collection_available
                    })
        return all_tests
    
    def check_lab_offers_test(self, test_name: str, lab_name: str) -> Optional[Dict]:
        """Check if a specific lab offers a specific test"""
        tests = self.db.search_tests(test_name)
        for test in tests:
            for lab in test.labs_offering:
                if lab_name.lower() in lab.lab_name.lower():
                    return {
                        'available': True,
                        'test_name': test.name,
                        'lab_name': lab.lab_name,
                        'price': lab.price,
                        'turnaround_time': lab.turnaround_time,
                        'home_collection_available': lab.home_collection_available,
                        'rating': lab.lab_rating
                    }
        return {'available': False}
    
    def get_test_details(self, test_id: str) -> Optional[Dict]:
        """Get detailed info about a test with all lab offerings"""
        test = self.db.get_test(test_id)
        if not test:
            return None
        
        labs_data = []
        for lab in test.labs_offering:
            labs_data.append({
                'lab_id': lab.lab_id,
                'lab_name': lab.lab_name,
                'lab_rating': lab.lab_rating,
                'lab_location': lab.lab_location,
                'price': lab.price,
                'home_collection_available': lab.home_collection_available,
                'home_collection_fee': lab.home_collection_fee,
                'turnaround_time': lab.turnaround_time,
                'accreditation': lab.accreditation
            })
        
        return {
            'id': test.id,
            'name': test.name,
            'category': test.category,
            'sample_type': test.sample_type,
            'fasting_required': test.fasting_required,
            'preparation_instructions': test.preparation_instructions,
            'parameters_count': test.parameters_count,
            'rating': test.rating,
            'booking_count': test.booking_count,
            'labs_offering': labs_data
        }
    
    def add_to_cart(self, session_id: str, test_id: str, lab_id: str) -> Dict:
        """Add a test from a specific lab to cart"""
        test = self.db.get_test(test_id)
        if not test:
            return {'success': False, 'message': f'Test {test_id} not found'}
        
        # Find the selected lab offering
        selected_lab = None
        for lab in test.labs_offering:
            if lab.lab_id == lab_id:
                selected_lab = lab
                break
        
        if not selected_lab:
            return {'success': False, 'message': f'Lab {lab_id} does not offer this test'}
        
        # Add to cart via session manager
        cart_item = {
            'test_id': test_id,
            'test_name': test.name,
            'lab_id': selected_lab.lab_id,
            'lab_name': selected_lab.lab_name,
            'price': selected_lab.price,
            'home_collection_available': selected_lab.home_collection_available,
            'turnaround_time': selected_lab.turnaround_time
        }
        
        self.session_manager.add_to_cart(session_id, cart_item)
        cart_total = self.session_manager.get_cart_total(session_id)
        state = self.session_manager.get_state(session_id)
        
        return {
            'success': True,
            'message': f'Added {test.name} from {selected_lab.lab_name} to cart',
            'cart': state['cart'],
            'cart_total': cart_total
        }
    
    def remove_from_cart(self, session_id: str, test_id: str) -> Dict:
        """Remove a test from cart"""
        state = self.session_manager.remove_from_cart(session_id, test_id)
        cart_total = self.session_manager.get_cart_total(session_id)
        
        return {
            'success': True,
            'message': 'Test removed from cart',
            'cart': state['cart'],
            'cart_total': cart_total
        }
    
    def view_cart(self, session_id: str) -> Dict:
        """View current cart contents"""
        state = self.session_manager.get_state(session_id)
        cart_total = self.session_manager.get_cart_total(session_id)
        
        return {
            'cart': state['cart'],
            'cart_total': cart_total,
            'cart_count': len(state['cart'])
        }
    
    def clear_cart(self, session_id: str) -> Dict:
        """Clear all items from cart"""
        self.session_manager.clear_cart(session_id)
        return {
            'success': True,
            'message': 'Cart cleared',
            'cart': [],
            'cart_total': 0
        }
    
    def recommend_packages(self, test_ids: List[str]) -> Optional[Dict]:
        """Recommend packages based on selected tests"""
        # Find matching packages
        for package in self.db.packages:
            # Check if user's tests are in a package
            overlap = set(test_ids) & set(package.tests_included)
            if len(overlap) >= 2:  # At least 2 tests match
                return {
                    'id': package.id,
                    'name': package.name,
                    'description': package.description,
                    'tests_included': package.tests_included,
                    'original_price': package.original_price,
                    'package_price': package.package_price,
                    'savings': package.savings,
                    'home_collection_available': package.home_collection_available
                }
        return None
    
    def get_available_slots(self, session_id: str) -> List[Dict]:
        """Get available time slots for cart items"""
        state = self.session_manager.get_state(session_id)
        
        if not state['cart']:
            return []
        
        # Generate slots based on cart items
        slots = self.db.get_available_slots()
        return [{'slot_id': s.slot_id, 'date': str(s.date), 'time': s.time, 
                 'lab_name': s.lab_name, 'lab_address': s.lab_address} for s in slots]
    
    def book_tests(self, session_id: str, collection_type: str, slot_id: str, 
                   user_name: str, contact: str, address: Optional[str] = None) -> Dict:
        """Book all tests in cart"""
        state = self.session_manager.get_state(session_id)
        
        if not state['cart']:
            return {'success': False, 'message': 'Cart is empty'}
        
        # Get slot details
        slot = next((s for s in self.db.get_available_slots() if s.slot_id == slot_id), None)
        if not slot:
            return {'success': False, 'message': 'Invalid slot'}
        
        # Calculate total
        cart_total = self.session_manager.get_cart_total(session_id)
        
        # Add home collection fee if applicable
        if collection_type == 'home':
            home_fee = sum(item.get('home_collection_fee', 50) 
                          for item in state['cart'] if item.get('home_collection_available', False))
            cart_total += home_fee
        
        # Create booking reference
        booking_ref = f"BK{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Update session with booking details
        self.session_manager.update_state(session_id, {
            'journey_step': 'post_booking',
            'booking_reference': booking_ref,
            'selected_slot': {'slot_id': slot_id, 'date': str(slot.date), 'time': slot.time}
        })
        
        # Clear cart after booking
        self.session_manager.clear_cart(session_id)
        
        return {
            'success': True,
            'booking_reference': booking_ref,
            'tests': [item['test_name'] for item in state['cart']],
            'labs': list(set(item['lab_name'] for item in state['cart'])),
            'total_amount': cart_total,
            'collection_type': collection_type,
            'scheduled_date': str(slot.date),
            'scheduled_time': slot.time,
            'contact': contact
        }
