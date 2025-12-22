from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from datetime import datetime, date

class Coordinates(BaseModel):
    lat: float = Field(..., description="Latitude between -90 and 90")
    lng: float = Field(..., description="Longitude between -180 and 180")

    @validator("lat")
    def validate_lat(cls, v):
        if not (-90 <= v <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @validator("lng")
    def validate_lng(cls, v):
        if not (-180 <= v <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        return v

class Location(BaseModel):
    city: str
    clinic_name: str
    address: str
    coordinates: Coordinates

class Slot(BaseModel):
    slot_id: str
    start_time: str  # Format: "HH:MM" 24hr
    end_time: str    # Format: "HH:MM" 24hr
    is_booked: bool = False

class DayAvailability(BaseModel):
    date: date
    slots: List[Slot]

class Fees(BaseModel):
    online: int = Field(..., ge=0)
    in_clinic: int = Field(..., ge=0)

class Doctor(BaseModel):
    id: str
    name: str
    specialty: str
    qualifications: List[str]
    experience_years: int = Field(..., ge=0)
    languages: List[str]
    location: Location
    fees: Fees
    rating: float = Field(..., ge=0, le=5)
    reviews_count: int = 0
    availability: List[DayAvailability]

class Appointment(BaseModel):
    appointment_id: str
    doctor_id: str
    patient_id: str
    slot_id: str
    date: date
    type: str # 'online' or 'in_clinic'
    status: str = "confirmed" # confirmed, cancelled, completed
