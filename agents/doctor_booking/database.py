from typing import List, Optional, Dict
from datetime import date, timedelta
import random
from .models import Doctor, Location, Coordinates, Fees, DayAvailability, Slot, Appointment
from .utils import haversine, calculate_relevance_score

CLASSIFICATIONS = [
    "Dermatologist", "General Physician", "Pediatrician", 
    "Orthopedist", "Cardiologist", "Dentist"
]

class MockDatabase:
    def __init__(self):
        self.doctors: Dict[str, Doctor] = {}
        self.appointments: Dict[str, Appointment] = {}
        self._seed_data()

    def _seed_data(self):
        """Populate DB with mock doctors across Pune limits"""
        
        # Base location: Pune Center (approx)
        base_lat = 18.5204
        base_lng = 73.8567
        
        # Generate 20 doctors
        for i in range(1, 21):
            doc_id = f"doc_{i:03d}"
            
            # Randomize location within ~10km radius
            lat_offset = random.uniform(-0.09, 0.09)
            lng_offset = random.uniform(-0.09, 0.09)
            
            # Randomize attributes
            specialty = random.choice(CLASSIFICATIONS)
            exp = random.randint(3, 25)
            rating = round(random.uniform(3.5, 5.0), 1)
            
            doctor = Doctor(
                id=doc_id,
                name=f"Dr. {random.choice(['Sharma', 'Patel', 'Gupta', 'Singh', 'Deshmukh', 'Kulkarni'])} ({i})",
                specialty=specialty,
                qualifications=["MBBS", "MD"],
                experience_years=exp,
                languages=["English", "Hindi", "Marathi"],
                location=Location(
                    city="Pune",
                    clinic_name=f"Clinic {i}",
                    address=f"Sector {random.randint(1, 50)}, Pune",
                    coordinates=Coordinates(
                        lat=base_lat + lat_offset,
                        lng=base_lng + lng_offset
                    )
                ),
                fees=Fees(
                    online=random.choice([400, 500, 800]),
                    in_clinic=random.choice([800, 1000, 1500])
                ),
                rating=rating,
                reviews_count=random.randint(50, 500),
                availability=self._generate_availability(),
                consultation_modes=random.choice([["clinic"], ["video", "clinic"], ["video", "clinic"]]) # High chance of both
            )
            self.doctors[doc_id] = doctor

    def _generate_availability(self) -> List[DayAvailability]:
        """Generate 7 days of slots"""
        availability = []
        today = date.today()
        
        for i in range(7):
            current_date = today + timedelta(days=i)
            slots = []
            # Create 4 slots per day
            times = [("10:00", "10:30"), ("11:00", "11:30"), ("17:00", "17:30"), ("18:00", "18:30")]
            
            for idx, (start, end) in enumerate(times):
                slots.append(Slot(
                    slot_id=f"slot_{i}_{idx}",
                    start_time=start,
                    end_time=end,
                    is_booked=random.choice([True, False, False]) # 33% chance booked
                ))
            
            availability.append(DayAvailability(date=current_date, slots=slots))
            
        return availability

    def search_doctors(self, 
                      user_lat: float, 
                      user_lng: float, 
                      query: str = None, 
                      filters: Dict = None) -> List[Dict]:
        """
        Search and rank doctors based on distance and criteria.
        Returns list of dicts with extra metadata (distance, score).
        """
        results = []
        
        for doc in self.doctors.values():
            # 1. Filter by Query (Specialty or Name)
            if query:
                q_str = query.lower()
                if q_str not in doc.specialty.lower() and q_str not in doc.name.lower():
                    continue
            
            # 2. Filter by Attributes
            if filters:
                if filters.get("max_fees") and doc.fees.in_clinic > filters["max_fees"]:
                    continue
                if filters.get("min_rating") and doc.rating < filters["min_rating"]:
                    continue
            
            # 3. Calculate Distance
            dist = haversine(
                user_lat, user_lng, 
                doc.location.coordinates.lat, 
                doc.location.coordinates.lng
            )
            
            # 4. Check Availability (Simplification: Check today/tomorrow)
            has_slots_today = any(not s.is_booked for s in doc.availability[0].slots)
            
            # 5. Score
            score = calculate_relevance_score(dist, doc.rating, has_slots_today)
            
            results.append({
                "doctor": doc,
                "distance_km": round(dist, 2),
                "score": score,
                "available_today": has_slots_today
            })
            
        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def get_doctor(self, doctor_id: str) -> Optional[Doctor]:
        return self.doctors.get(doctor_id)

    def book_slot(self, doctor_id: str, date_str: str, slot_id: str, patient_id: str) -> Dict:
        """Attempt to book a slot"""
        doc = self.doctors.get(doctor_id)
        if not doc:
            return {"status": "error", "message": "Doctor not found"}
            
        # Find the slot
        target_date = date.fromisoformat(date_str)
        day_avail = next((d for d in doc.availability if d.date == target_date), None)
        
        if not day_avail:
             return {"status": "error", "message": "Date not available"}
             
        slot = next((s for s in day_avail.slots if s.slot_id == slot_id), None)
        
        if not slot:
            return {"status": "error", "message": "Slot not found"}
            
        if slot.is_booked:
            return {"status": "error", "message": "Slot already booked"}
            
        # Book it
        slot.is_booked = True
        
        appt_id = f"appt_{len(self.appointments) + 1}"
        appt = Appointment(
            appointment_id=appt_id,
            doctor_id=doctor_id,
            patient_id=patient_id,
            slot_id=slot_id,
            date=target_date,
            type="in_clinic"
        )
        self.appointments[appt_id] = appt
        
        return {
            "status": "success", 
            "appointment_id": appt_id,
            "message": f"Booked with {doc.name}"
        }
