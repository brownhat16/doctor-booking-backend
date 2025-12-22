from typing import List, Dict, Optional
from .database import MockDatabase
from .models import Coordinates

class DoctorBookingAgent:
    def __init__(self):
        self.db = MockDatabase()
        
    def find_doctors(self, 
                    intent: str, 
                    user_lat: float, 
                    user_lng: float, 
                    filters: Dict = None,
                    llm_service = None) -> List[Dict]:
        """
        High-level tool called by orchestrator.
        intent: Natural language query (e.g., "cheap cardiologist")
        """
        parsed_filters = filters or {}
        
        # If LLM service is provided, refine the intent
        if llm_service and " " in intent:
            print(f"DEBUG: Using LLM to parse intent: '{intent}'")
            parsed_intent = llm_service.parse_doctor_search_intent(intent)
            print(f"DEBUG: Extracted Filters: {parsed_intent}")
            
            # Update query to the extracted specialty/keyword
            intent = parsed_intent.get("query", intent)
            
            # Merge extracted filters
            if parsed_intent.get("max_fees"):
                parsed_filters["max_fees"] = parsed_intent["max_fees"]
            if parsed_intent.get("min_rating"):
                parsed_filters["min_rating"] = parsed_intent["min_rating"]

        raw_results = self.db.search_doctors(user_lat, user_lng, query=intent, filters=parsed_filters)
        
        # Format results for the chat interface
        formatted = []
        for res in raw_results[:5]: # Top 5
            doc = res["doctor"]
            formatted.append({
                "id": doc.id,
                "name": doc.name,
                "specialty": doc.specialty,
                "distance": f"{res['distance_km']} km",
                "next_available": "Today" if res["available_today"] else "Tomorrow",
                "rating": doc.rating,
                "fees": doc.fees.in_clinic,
                "match_reason": f"Rated {doc.rating} stars and close to you."
            })
            
        return formatted

    def get_doctor_schedule(self, doctor_id: str) -> Dict:
        """Get availability for a specific doctor"""
        doc = self.db.get_doctor(doctor_id)
        if not doc:
            return {"error": "Doctor not found"}
            
        schedule = []
        for day in doc.availability[:3]: # Next 3 days only
            slots = [s for s in day.slots if not s.is_booked]
            if slots:
                schedule.append({
                    "date": day.date.isoformat(),
                    "slots": [{"id": s.slot_id, "time": f"{s.start_time}-{s.end_time}"} for s in slots]
                })
                
        return {
            "doctor": doc.name,
            "schedule": schedule
        }

    def book_appointment(self, doctor_id: str, date_str: str, slot_id: str, patient_id: str) -> Dict:
        """Final booking step"""
        return self.db.book_slot(doctor_id, date_str, slot_id, patient_id)
