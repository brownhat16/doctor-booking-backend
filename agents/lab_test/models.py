from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date

class LabTest(BaseModel):
    """Individual lab test model"""
    id: str
    name: str
    category: str  # "Blood Tests", "Radiology", "Organ Function", etc.
    price: int
    home_collection_available: bool
    home_collection_fee: Optional[int] = 0
    sample_type: str  # "Blood", "Urine", "Stool", "Tissue", etc.
    fasting_required: bool
    preparation_instructions: str
    turnaround_time: str  # "24 hours", "Same day", "48 hours"
    parameters_count: int  # Number of parameters measured
    rating: float
    booking_count: int  # Popularity metric
    
class LabPackage(BaseModel):
    """Test package model (e.g., Full Body Checkup)"""
    id: str
    name: str
    description: str
    tests_included: List[str]  # List of test IDs
    original_price: int  # Sum of individual test prices
    package_price: int  # Discounted package price
    savings: int  # original_price - package_price
    home_collection_available: bool
    home_collection_fee: Optional[int] = 0
    category: str
    popular: bool = False
    
class LabSlot(BaseModel):
    """Sample collection slot model"""
    slot_id: str
    date: str  # ISO format: "2025-12-24"
    time_range: str  # "08:00-09:00 AM"
    collection_type: str  # "home" or "lab"
    available: bool
    lab_name: Optional[str] = None  # For lab visits
    lab_address: Optional[str] = None

class CartItem(BaseModel):
    """Item in booking cart (for multiple test booking)"""
    item_id: str  # Test ID or Package ID
    item_type: str  # "test" or "package"
    name: str
    price: int
    
class LabBooking(BaseModel):
    """Lab test booking model"""
    booking_id: str
    items: List[CartItem]
    total_price: int
    collection_type: str  # "home" or "lab"
    collection_slot: LabSlot
    user_name: str
    user_phone: str
    user_address: Optional[str] = None  # For home collection
    status: str = "confirmed"
    created_at: datetime = Field(default_factory=datetime.now)
