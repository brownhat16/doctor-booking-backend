from typing import List, Dict, Optional
from .database import LabTestDatabase
from .models import LabTest, LabPackage, LabSlot, CartItem, LabBooking
import random
from datetime import datetime

class LabTestAgent:
    def __init__(self):
        self.db = LabTestDatabase()
        self.cart: Dict[str, List[CartItem]] = {}  # session_id -> cart items
    
    def search_tests(self, query: str, filters: Optional[Dict] = None) -> List[Dict]:
        """Search for lab tests"""
        results = self.db.search_tests(query, filters)
        
        # Format for frontend
        formatted = []
        for test in results[:10]:  # Top 10 results
            formatted.append({
                "id": test.id,
                "name": test.name,
                "category": test.category,
                "price": test.price,
                "home_collection_available": test.home_collection_available,
                "home_collection_fee": test.home_collection_fee,
                "sample_type": test.sample_type,
                "fasting_required": test.fasting_required,
                "preparation_instructions": test.preparation_instructions,
                "turnaround_time": test.turnaround_time,
                "parameters_count": test.parameters_count,
                "rating": test.rating,
                "booking_count": test.booking_count
            })
        
        return formatted
    
    def get_test_details(self, test_id: str) -> Optional[Dict]:
        """Get detailed info about a test"""
        test = self.db.get_test(test_id)
        if not test:
            return None
        
        return {
            "id": test.id,
            "name": test.name,
            "category": test.category,
            "price": test.price,
            "home_collection_available": test.home_collection_available,
            "home_collection_fee": test.home_collection_fee,
            "sample_type": test.sample_type,
            "fasting_required": test.fasting_required,
            "preparation_instructions": test.preparation_instructions,
            "turnaround_time": test.turnaround_time,
            "parameters_count": test.parameters_count,
            "rating": test.rating,
            "booking_count": test.booking_count
        }
    
    def recommend_package(self, test_ids: List[str]) -> Optional[Dict]:
        """Check if selected tests can be combined into a package"""
        package = self.db.recommend_package(test_ids)
        if not package:
            return None
        
        # Get full test details for the package
        included_tests = []
        for test_id in package.tests_included:
            test = self.db.get_test(test_id)
            if test:
                included_tests.append({
                    "id": test.id,
                    "name": test.name,
                    "price": test.price
                })
        
        return {
            "id": package.id,
            "name": package.name,
            "description": package.description,
            "tests_included": included_tests,
            "original_price": package.original_price,
            "package_price": package.package_price,
            "savings": package.savings,
            "savings_percentage": round((package.savings / package.original_price) * 100),
            "home_collection_available": package.home_collection_available,
            "home_collection_fee": package.home_collection_fee
        }
    
    def add_to_cart(self, session_id: str, item_id: str, item_type: str) -> Dict:
        """Add test or package to cart"""
        if session_id not in self.cart:
            self.cart[session_id] = []
        
        # Get item details
        if item_type == "test":
            test = self.db.get_test(item_id)
            if not test:
                return {"status": "error", "message": "Test not found"}
            item = CartItem(
                item_id=test.id,
                item_type="test",
                name=test.name,
                price=test.price
            )
        elif item_type == "package":
            package = self.db.get_package(item_id)
            if not package:
                return {"status": "error", "message": "Package not found"}
            item = CartItem(
                item_id=package.id,
                item_type="package",
                name=package.name,
                price=package.package_price
            )
        else:
            return {"status": "error", "message": "Invalid item type"}
        
        # Add to cart
        self.cart[session_id].append(item)
        total = sum(i.price for i in self.cart[session_id])
        
        return {
            "status": "success",
            "cart_count": len(self.cart[session_id]),
            "total_price": total,
            "items": [{"name": i.name, "price": i.price} for i in self.cart[session_id]]
        }
    
    def get_available_slots(self, collection_type: str) -> List[Dict]:
        """Get available time slots"""
        slots = self.db.get_available_slots(collection_type)
        
        return [{
            "slot_id": s.slot_id,
            "date": s.date,
            "time_range": s.time_range,
            "collection_type": s.collection_type,
            "lab_name": s.lab_name,
            "lab_address": s.lab_address
        } for s in slots[:20]]  # Return 20 slots
    
    def book_tests(
        self,
        session_id: str,
        collection_type: str,
        slot_id: str,
        user_name: str,
        user_phone: str,
        user_address: Optional[str] = None
    ) -> Dict:
        """Book lab tests"""
        
        # Get cart
        if session_id not in self.cart or not self.cart[session_id]:
            return {"status": "error", "message": "Cart is empty"}
        
        # Get slot
        slots = self.db.get_available_slots(collection_type)
        slot = next((s for s in slots if s.slot_id == slot_id), None)
        if not slot:
            return {"status": "error", "message": "Slot not available"}
        
        # Calculate total
        total_price = sum(item.price for item in self.cart[session_id])
        if collection_type == "home":
            total_price += 50  # Home collection fee
        
        # Create booking
        booking_id = f"lab_booking_{random.randint(1000, 9999)}"
        
        booking = LabBooking(
            booking_id=booking_id,
            items=self.cart[session_id],
            total_price=total_price,
            collection_type=collection_type,
            collection_slot=slot,
            user_name=user_name,
            user_phone=user_phone,
            user_address=user_address if collection_type == "home" else None,
            status="confirmed"
        )
        
        # Clear cart
        self.cart[session_id] = []
        
        return {
            "status": "success",
            "booking_id": booking_id,
            "items": [{"name": i.name, "price": i.price} for i in booking.items],
            "total_price": total_price,
            "collection_type": collection_type,
            "slot": {
                "date": slot.date,
                "time_range": slot.time_range,
                "lab_name": slot.lab_name,
                "lab_address": slot.lab_address
            }
        }
