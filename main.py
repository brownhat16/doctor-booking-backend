from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
from agents.doctor_booking.agent import DoctorBookingAgent
from agents.llm_service import LLMService

app = FastAPI(title="Doctor Booking API", version="1.0.0")

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
agent = DoctorBookingAgent()

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
    Supports search, filter, slots, booking, and chat intents.
    """
    try:
        # Convert history to format expected by LLM
        history_tuples = [(msg.role.capitalize(), msg.content) for msg in request.history]
        
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

            results = agent.find_doctors(query, lat, lng, filters=filters)

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

        
        # Handle filter intent
        if intent_type == "filter":
            # Note: Filtering requires cached results from frontend
            # This is a simplified version - real implementation would need session management
            return ChatResponse(
                type="filter",
                message="Filtering requires cached results. Please use the frontend filter logic."
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
            candidates = agent.find_doctors(doctor_name, lat, lng)
            if not candidates:
                return ChatResponse(
                    type="chat",
                    message=f"I couldn't find a doctor named '{doctor_name}'."
                )
            
            doc_id = candidates[0]['id']
            schedule = agent.get_doctor_schedule(doc_id)
            
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
            candidates = agent.find_doctors(doctor_name, lat, lng)
            if not candidates:
                return ChatResponse(
                    type="chat",
                    message=f"I couldn't find a doctor named '{doctor_name}'."
                )
            
            doc_id = candidates[0]['id']
            schedule = agent.get_doctor_schedule(doc_id)
            
            if not schedule.get("schedule"):
                return ChatResponse(
                    type="chat",
                    message="Sorry, this doctor has no available slots."
                )
            
            # Auto-book first available slot
            first_slot = schedule['schedule'][0]['slots'][0]
            date_str = schedule['schedule'][0]['date']
            
            result = agent.book_appointment(doc_id, date_str, first_slot['id'], "web_user")
            
            if result['status'] == 'success':
                message = f"✅ Success! Appointment ID: {result['appointment_id']}\n"
                message += f"Confirmed with {schedule['doctor']} for {date_str} at {first_slot['time']}.\n"
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

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
