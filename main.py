from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
from agents.doctor_booking.agent import DoctorBookingAgent
from agents.lab_test.agent import LabTestAgent
from agents.llm_service import LLMService

app = FastAPI(title="Healthcare Booking API", version="2.0.0")

# CORS middleware to allow Next.js frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your Vercel domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents
api_key = os.getenv("NVIDIA_API_KEY")
if not api_key:
    raise ValueError("NVIDIA_API_KEY environment variable is required")

llm = LLMService(api_key=api_key)
doctor_agent = DoctorBookingAgent()
lab_agent = LabTestAgent()

# Request/Response models
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[Message]
    userLocation: Dict[str, float]

class ChatResponse(BaseModel):
    type: str
    message: str
    data: Optional[Dict[str, Any]] = None

@app.get("/")
async def root():
    return {
        "service": "Doctor Booking API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/specialties")
async def get_specialties():
    """Return list of supported medical specialties"""
    # Matching the frontend list
    return [
        "General Physician", "Dermatologist", "Homeopathy", "Orthopaedic", 
        "Ayurveda", "Dentist", "Gynaecologist", "Ear, Nose, Throat", 
        "Paediatrician", "Psychiatrist"
    ]

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint that handles all user messages.
    Supports both doctor and lab test queries.
    """
    try:
        # Convert history to format expected by LLM
        history_tuples = [(msg.role.capitalize(), msg.content) for msg in request.history]
        
        # Detect query type (doctor vs lab test)
        lower_msg = request.message.lower()
        lab_keywords = ["test", "lab", "blood", "cbc", "thyroid", "diabetes", "hba1c", 
                       "lipid", "liver", "kidney", "vitamin", "x-ray", "ultrasound", 
                       "ct scan", "mri", "ecg", "covid", "pregnancy"]
        
        is_lab_query = any(keyword in lower_msg for keyword in lab_keywords)
        
        # Route to appropriate agent
        if is_lab_query:
            # Handle lab test queries
            return await handle_lab_test_query(request, history_tuples)
        else:
            # Handle doctor queries (existing logic)
            return await handle_doctor_query(request, history_tuples)
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

async def handle_doctor_query(request: ChatRequest, history_tuples: list):
    """Handle doctor booking queries"""
    try:
        # Parse intent with LLM
        intent_data = llm.parse_doctor_search_intent(request.message, history_tuples)
        
        intent_type = intent_data.get("type", "").lower().strip()
        print(f"DEBUG: Parsed Intent Type: '{intent_type}'")
        print(f"DEBUG: Full Intent Data: {intent_data}")
        
        lat = request.userLocation.get("lat", 18.5204)
        lng = request.userLocation.get("lng", 73.8567)
        
        # Handle chat intent
        if intent_type == "chat":
            return ChatResponse(
                type="chat",
                message=intent_data.get("response", "Hello! How can I help you?")
            )
        
        # Handle search intent
        if intent_type == "search":
            # Detect consultation mode (video or in-clinic) from user message
            lower_msg = request.message.lower()
            if "video" in lower_msg:
                consultation_mode = "video"
            elif "clinic" in lower_msg or "in-clinic" in lower_msg:
                consultation_mode = "clinic"
            else:
                consultation_mode = None

            # Apply simple filter placeholder (could be extended with real data)
            if consultation_mode:
                # For demonstration, we just note the mode in the response message
                mode_note = f" (Preferred mode: {consultation_mode})"
            else:
                mode_note = ""

            query = intent_data.get("query", request.message)
            filters_obj = intent_data.get("filters", {})
            filters = {}
            if filters_obj.get("max_fees"):
                filters["max_fees"] = filters_obj["max_fees"]
            if filters_obj.get("min_rating"):
                filters["min_rating"] = filters_obj["min_rating"]

            results = doctor_agent.find_doctors(query, lat, lng, filters=filters)

            if not results:
                return ChatResponse(
                    type="search",
                    message=f"I couldn't find any doctors matching '{query}'. Try a different specialty?",
                )

            # Optionally filter by consultation mode if data supports it (placeholder)
            if consultation_mode:
                # Assuming each doctor dict may have a 'consultation_modes' list
                filtered = [doc for doc in results if consultation_mode in doc.get('consultation_modes', [])]
                if filtered:
                    results = filtered

            top_result = results[0]
            count = len(results)

            message = f"I found {count} doctors. The best match is {top_result['name']} ({top_result['specialty']}).\n"
            message += f"They are {top_result['distance']} away and rated {top_result['rating']} stars.\n\n"
            message += "Here are the top options:" + mode_note

            return ChatResponse(
                type="search",
                message=message,
                data={
                    "doctors": results[:5],  # Return top 5
                    "count": count
                }
            )
        
        # Handle filter intent
        if intent_type == "filter":
            # Extract filter parameters from LLM intent
            filters_obj = intent_data.get("filters", {})
            filters = {}
            if filters_obj.get("max_fees"):
                filters["max_fees"] = filters_obj["max_fees"]
            if filters_obj.get("min_rating"):
                filters["min_rating"] = filters_obj["min_rating"]
            
            # Note: We need to know what specialty was searched before
            # For simplicity, we'll ask the user to specify the specialty again
            # A production system would cache this in session state
            
            # Extract query from previous context or ask user
            query = intent_data.get("query")
            if not query:
                return ChatResponse(
                    type="chat",
                    message="What specialty of doctor are you filtering for? (e.g., Dermatologist, General Physician)"
                )
            
            # Perform search with filters
            results = doctor_agent.find_doctors(query, lat, lng, filters=filters)
            
            if not results:
                return ChatResponse(
                    type="search",
                    message=f"I couldn't find any doctors matching your criteria. Try adjusting your filters?",
                )
            
            top_result = results[0]
            count = len(results)
            
            filter_desc = []
            if filters.get("max_fees"):
                filter_desc.append(f"under ₹{filters['max_fees']}")
            if filters.get("min_rating"):
                filter_desc.append(f"{filters['min_rating']}+ stars")
            
            filter_text = " and ".join(filter_desc) if filter_desc else "your criteria"
            
            message = f"Found {count} doctors matching {filter_text}.\n\n"
            message += f"Top match: {top_result['name']} ({top_result['specialty']}) - "
            message += f"₹{top_result['fees']}, {top_result['rating']} stars, {top_result['distance']} away."
            
            return ChatResponse(
                type="search",
                message=message,
                data={
                    "doctors": results[:5],
                    "count": count
                }
            )
        
        # Handle slots intent
        if intent_type == "slots":
            doctor_name = intent_data.get("query")
            if not doctor_name:
                return ChatResponse(
                    type="chat",
                    message="Which doctor would you like to see the schedule for?"
                )
            
            # Find doctor by name
            candidates = doctor_agent.find_doctors(doctor_name, lat, lng)
            if not candidates:
                return ChatResponse(
                    type="chat",
                    message=f"I couldn't find a doctor named '{doctor_name}'."
                )
            
            doc_id = candidates[0]['id']
            schedule = doctor_agent.get_doctor_schedule(doc_id)
            
            if not schedule.get("schedule"):
                return ChatResponse(
                    type="chat",
                    message="Sorry, this doctor has no available slots."
                )
            
            return ChatResponse(
                type="slots",
                message=f"Schedule for {schedule['doctor']}",
                data=schedule
            )
        
        # Handle booking intent
        if intent_type == "booking":
            doctor_name = intent_data.get("query")
            if not doctor_name:
                return ChatResponse(
                    type="chat",
                    message="Who would you like to book an appointment with?"
                )
            
            # Find doctor
            candidates = doctor_agent.find_doctors(doctor_name, lat, lng)
            if not candidates:
                return ChatResponse(
                    type="chat",
                    message=f"I couldn't find a doctor named '{doctor_name}'."
                )
            
            doc_id = candidates[0]['id']
            schedule = doctor_agent.get_doctor_schedule(doc_id)
            
            if not schedule.get("schedule"):
                return ChatResponse(
                    type="chat",
                    message="Sorry, this doctor has no available slots."
                )
            
            # Auto-book first available slot
            first_slot = schedule['schedule'][0]['slots'][0]
            date_str = schedule['schedule'][0]['date']
            
            result = doctor_agent.book_appointment(doc_id, date_str, first_slot['id'], "web_user")
            
            if result['status'] == 'success':
                # Detect consultation mode from the original request
                lower_msg = request.message.lower()
                is_video = "video" in lower_msg
                
                message = f"✅ Success! Appointment ID: {result['appointment_id']}\n"
                message += f"Confirmed with {schedule['doctor']} for {date_str} at {first_slot['time']}.\n"
                
                # Context-aware instruction based on consultation type
                if is_video:
                    message += "\n📹 **Video Consultation**\n"
                    message += "The video call link will be sent to you via SMS and email immediately after booking.\n"
                    message += "Please join the call 5 mins early."
                else:
                    # Get doctor location for maps link
                    doctor_obj = doctor_agent.db.get_doctor(doc_id)
                    if doctor_obj:
                        lat = doctor_obj.location.coordinates.lat
                        lng = doctor_obj.location.coordinates.lng
                        clinic_name = doctor_obj.location.clinic_name
                        address = doctor_obj.location.address
                        
                        # Generate Google Maps link
                        maps_link = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}"
                        
                        message += "\n🏥 **In-Clinic Consultation**\n"
                        message += f"📍 {clinic_name}\n"
                        message += f"{address}\n\n"
                        message += f"🗺️ Get Directions: {maps_link}\n\n"
                        message += "Please arrive 15 mins early."
                    else:
                        message += "Please arrive 15 mins early."
            else:
                message = f"❌ Booking failed: {result['message']}"
            
            return ChatResponse(
                type="booking",
                message=message,
                data=result
            )
        
        # Fallback
        return ChatResponse(
            type="chat",
            message="I'm not sure how to help with that. Try telling me your symptoms or the specialty you're looking for!"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def handle_lab_test_query(request: ChatRequest, history_tuples: list):
    """Handle lab test booking queries with stateful cart"""
    session_id = request.userLocation.get("session_id", "default_session")
    session_state = lab_agent.session_manager.get_state(session_id)
    intent_data = llm.parse_lab_test_intent(request.message, history_tuples, session_state)
    intent_type = intent_data.get("type", "").lower().strip()
    print(f"LAB: Intent={intent_type}, Cart={len(session_state['cart'])}")
    
    if intent_type == "chat":
        return ChatResponse(type="chat", message=intent_data.get("response", "How can I help?"))
    
    if intent_type == "search":
        query = intent_data.get("query", "")
        if isinstance(query, list):
            query = " ".join(query)
        results = lab_agent.search_tests(query, session_id, intent_data.get("filters", {}))
        if not results:
            return ChatResponse(type="search", message=f"No tests found for '{query}'")
        return ChatResponse(type="search", message=f"Found {len(results)} test(s)", 
                           data={"tests": results, "session_id": session_id})
    
    if intent_type == "add_to_cart":
        result = lab_agent.add_to_cart(session_id, intent_data.get("test_id"), intent_data.get("lab_id"))
        cart_data = lab_agent.view_cart(session_id)
        # Better response with next steps
        msg = f"✅ {result['message']}\n\n"
        msg += f"🛒 **Your Cart:** {cart_data['cart_count']} test(s), Total: ₹{cart_data['cart_total']}\n\n"
        msg += "What would you like to do next?\n"
        msg += "• Search for more tests\n"
        msg += "• Say **'view cart'** to see all items\n"
        msg += "• Say **'proceed to book'** when ready"
        return ChatResponse(type="cart_updated", message=msg, data=result)
    
    if intent_type == "view_cart":
        cart_data = lab_agent.view_cart(session_id)
        if not cart_data['cart']:
            return ChatResponse(type="chat", message="Your cart is empty. Search for tests to add!")
        msg = f"🛒 **Your Cart:** {cart_data['cart_count']} test(s)\n\n"
        for item in cart_data['cart']:
            msg += f"• {item['test_name']} from {item['lab_name']} - ₹{item['price']}\n"
        msg += f"\n**Total: ₹{cart_data['cart_total']}**\n\n"
        msg += "Say **'proceed to book'** when ready!"
        return ChatResponse(type="cart_view", message=msg, data=cart_data)
    
    if intent_type == "availability":
        # User wants to see available slots
        cart_data = lab_agent.view_cart(session_id)
        if not cart_data['cart']:
            return ChatResponse(type="chat", message="Your cart is empty. Add tests before checking availability!")
        
        slots = lab_agent.get_available_slots(session_id)
        if not slots:
            return ChatResponse(type="chat", message="No slots available currently. Please try again later.")
        
        # Group slots by date for display
        msg = f"📅 **Available Slots for {cart_data['cart_count']} test(s)**\n\n"
        msg += f"💰 Total: ₹{cart_data['cart_total']}\n\n"
        msg += "Please select a date and time slot from the options below:"
        
        return ChatResponse(
            type="lab_slots", 
            message=msg, 
            data={"slots": slots, "cart": cart_data}
        )
    
    if intent_type == "booking":
        # User wants to book with selected slot
        cart_data = lab_agent.view_cart(session_id)
        if not cart_data['cart']:
            return ChatResponse(type="chat", message="Your cart is empty. Add tests first!")
        
        slot_id = intent_data.get("slot_id")
        date = intent_data.get("date")
        time = intent_data.get("time")
        collection_type = intent_data.get("collection_type", "lab_visit")
        
        # Generate booking reference
        import random
        import string
        booking_ref = "LB" + "".join(random.choices(string.digits, k=8))
        
        # Calculate total with home collection fee if applicable
        total = cart_data['cart_total']
        home_fee = 0
        if collection_type == "home_collection":
            home_fee = 50  # Standard home collection fee
            total += home_fee
        
        booking_result = {
            "success": True,
            "booking_reference": booking_ref,
            "tests": cart_data['cart'],
            "date": date or "Tomorrow",
            "time": time or "9:00 AM - 11:00 AM",
            "collection_type": collection_type,
            "total": total,
            "home_collection_fee": home_fee if collection_type == "home_collection" else 0
        }
        
        # Clear cart after booking
        lab_agent.clear_cart(session_id)
        
        msg = f"✅ **Booking Confirmed!**\n\n"
        msg += f"📋 **Booking Reference:** `{booking_ref}`\n\n"
        msg += f"**Tests Booked:**\n"
        for item in booking_result['tests']:
            msg += f"• {item['test_name']} from {item['lab_name']}\n"
        msg += f"\n📅 **Date:** {booking_result['date']}\n"
        msg += f"⏰ **Time:** {booking_result['time']}\n"
        msg += f"🏠 **Collection:** {'Home Sample Collection' if collection_type == 'home_collection' else 'Lab Visit'}\n"
        if home_fee > 0:
            msg += f"🚗 **Home Collection Fee:** ₹{home_fee}\n"
        msg += f"\n💰 **Total Amount:** ₹{total}\n\n"
        msg += "You will receive an SMS confirmation shortly. Thank you!"
        
        return ChatResponse(type="booking_confirmed", message=msg, data=booking_result)
    
    return ChatResponse(type="chat", message="Search tests, add to cart, or ask questions!")


if __name__ == "__main__":

    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
