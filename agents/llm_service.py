import json
from typing import Dict, Any
from openai import OpenAI

class LLMService:
    def __init__(self, api_key: str):
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key
        )
        self.doctor_model = "deepseek-ai/deepseek-v3.1"
        self.lab_model = "openai/gpt-oss-120b"

    def parse_doctor_search_intent(self, user_query: str, history: list = None) -> Dict[str, Any]:
        """
        Uses DeepSeek V3.1 (via NVIDIA) to extract structured filters from natural language query.
        """
        history_text = "\n".join([f"{role}: {msg}" for role, msg in (history or [])])
        
        system_prompt = """
You are an intelligent intent parser for a healthcare chatbot.

SYSTEM ROLE:
You help users find doctors, understand appointment slots (availability), and book appointments.
You DO NOT invent doctors, slots, fees, ratings, or availability.

CRITICAL RULES:
- NEVER hallucinate doctor names, slot IDs, fees, ratings, or availability.
- ONLY extract information explicitly mentioned by the user or clearly present in conversation history.
- If required information is missing, downgrade intent to "chat" and ask a clarification question.
- Return STRICTLY valid JSON. No markdown. No explanations. No comments.

OUTPUT STRUCTURE:
{
  "type": "search | filter | slots | booking | chat",
  "query": "specialty name or null",
  "filters": {
    "max_fees": <number or null>,
    "min_rating": <number or null>,
    "availability_time": <string or null>,
    "distance_km": <number or null>
  },
  "slot_id": "<slot identifier or null>",
  "response": "<Only for type='chat', your reply to the user>"
}

CONVERSATION CONTEXT:
If NO doctors shown yet → "filter" is DISABLED (use "search" or "chat" instead).

INTENT TYPES:

1. "search":
   - Initial doctor discovery by specialty OR symptoms
   - Changing specialty after doctors already shown
   - Examples: "I have fever", "Find a cardiologist", "Need a skin doctor"
   - Can include initial constraints (fees, rating, availability)

2. "filter":
   - **ONLY when doctors already shown in conversation**
   - User refines/narrows EXISTING results
   - Examples: "available after 5 pm", "under ₹500", "4 stars and above", "closer to me"
   - **EXCLUDE: Consultation mode questions like "are they available for video?" → Use "chat" instead**
   - NO new specialty mentioned
   - **IMPORTANT: Extract the specialty from conversation history** (e.g., if user searched for "cardiologist" before, query should be "Cardiologist")
   - NEVER use filter if no doctors in history

3. "slots":
   - User asks about specific doctor's schedule/availability
   - Examples: "What are the slots for Dr. X?", "Is he available tomorrow?", "Show his schedule"
   - Requires doctor name (explicit or from pronoun)

4. "booking":
   - User explicitly commits to booking AND provides:
     - Doctor name (explicit or resolved from context)
     - Specific time or slot identifier
   - If slot/time is missing → DO NOT use booking
   - Examples: "Book Dr. Patel at 5pm", "Confirm appointment for 3:30"

5. "chat":
   - Greetings, vague requests, clarifications, or missing information
   - **Consultation mode preferences without specialty** (e.g., "I want video consultation", "I prefer in-clinic")
   - Examples: "Hello", "I want to see a doctor" (no specialty), "Book an appointment" (no doctor/slot)
   - Use as fail-safe when intent is ambiguous

DECISION LOGIC:

Step 1: Check conversation history for "Found X doctors"
  - If NOT found → "filter" is DISABLED

Step 2: Analyze user query
  - **ONLY consultation mode mentioned (video/clinic) with NO specialty?** → "chat" (ask for specialty)
  - New specialty mentioned? → "search"
  - Refinement/constraint only? → "filter" (if doctors shown) OR "chat" (if not)
  - Asking about specific doctor slots? → "slots"
  - Committing to book with time? → "booking"
  - Vague/unclear? → "chat"


SYMPTOM → SPECIALIST MAPPING:
- Fever / Cold / Headache / GP → "General Physician"
- Skin / Hair / Acne / Pimple → "Dermatologist"
- Heart / Chest pain / BP → "Cardiologist"
- Kids / Baby / Child issues → "Pediatrician"
- Teeth / Dental / Root canal → "Dentist"
- Bone / Joint / Fracture / Ortho / Knee → "Orthopedist"
- Mental health / Depression / Anxiety / Therapist → "Psychiatrist"
- Women's health / Pregnancy / Period issues → "Gynaecologist"
- Ear / Nose / Throat / Cold / Sinus → "Ear, Nose, Throat"
- Ayurveda / Natural / Herbal → "Ayurveda"
- Homeopathy / Sweet pills → "Homeopathy"
- Multiple or unclear symptoms → type="chat"

PRONOUN RESOLUTION:
- Scan history for last mentioned doctor name
- Replace "him", "her", "them", "this doctor", "that one" with actual name
- If multiple doctors, choose the most recently mentioned
- If ambiguous, ask: "Which doctor are you referring to?"

FAIL-SAFE RULE:
If intent is ambiguous, required data is missing, or you're unsure:
→ return type="chat" with a helpful clarification question

EXAMPLES:

User: "I have fever" (no history)
Output: {"type": "search", "query": "General Physician", "filters": {}, ...}

User: (after doctors shown) "available after 5 pm"
Output: {"type": "filter", "query": "Dermatologist", "filters": {"availability_time": "5pm"}, ...}
// Note: "Dermatologist" extracted from conversation history where user searched for dermatologists

User: (after searching "cardiologist") "under ₹500"
Output: {"type": "filter", "query": "Cardiologist", "filters": {"max_fees": 500}, ...}
// Note: "Cardiologist" extracted from previous search

User: (no doctors shown) "available after 5 pm"
Output: {"type": "chat", "query": null, "response": "What specialty of doctor are you looking for?", ...}

User: (no doctors shown) "I want a video consultation"
Output: {"type": "chat", "query": null, "response": "Great! What kind of doctor are you looking for? (e.g., General Physician, Dermatologist, Cardiologist)", ...}

User: (no doctors shown) "I prefer in-clinic visit"
Output: {"type": "chat", "query": null, "response": "Understood! Which specialty doctor would you like to see?", ...}

User: (after doctors shown) "are they available in-clinic?"
Output: {"type": "chat", "query": null, "response": "Yes, all the doctors shown support in-clinic consultations. You can see their availability by clicking 'View Slots'. Would you like me to show you slots for a specific doctor?", ...}

User: (after doctors shown) "can I do video consultation with them?"
Output: {"type": "chat", "query": null, "response": "Most of these doctors support video consultations. To check a specific doctor's consultation modes and availability, click 'View Slots' on their card.", ...}

User: "What are the slots for Dr. Patel?"
Output: {"type": "slots", "query": "Dr. Patel", ...}

User: "Book Dr. Patel at 5:30pm"
Output: {"type": "booking", "query": "Dr. Patel", "slot_id": "5:30pm", ...}
"""
        
        user_prompt = f"""
        Conversation History:
        {history_text}
        
        Current User Query: "{user_query}"
        
        JSON Output:
        """

        try:
            completion = self.client.chat.completions.create(
                model=self.doctor_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                top_p=0.7,
                max_tokens=512
            )
            text = completion.choices[0].message.content.strip()
            # Remove markdown code fences if present
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                text = text.rsplit("\n```", 1)[0]
            return json.loads(text)
        except Exception as e:
            print(f"LLM Parsing Error: {e}")
            # Fallback
            return {"type": "search", "query": user_query, "max_fees": None, "availability": None}

    def parse_lab_test_intent(self, user_query: str, history: list = None, session_state: dict = None) -> Dict[str, Any]:
        """
        Uses GPT-OSS-120B (via NVIDIA) to parse lab test queries with stateful cart management.
        """
        history_text = "\n".join([f"{role}: {msg}" for role, msg in (history or [])])
        state_text = f"Current State: {session_state}" if session_state else "Current State: empty"
        
        system_prompt = """
You are an intelligent, stateful healthcare diagnostics assistant for lab test booking only (blood and urine diagnostics).
You guide users through test discovery → cart building → availability → booking → post-booking.
You must never hallucinate test names, prices, lab names, ratings, availability, or slot IDs.
You must always return STRICTLY valid JSON.

SCOPE & RESTRICTIONS:
- Supported: Lab diagnostics (blood/urine tests)
- Not supported: CT, MRI, X-ray, radiology (redirect to doctor booking)
- Do NOT auto-add items to cart
- Do NOT skip journey steps
- Do NOT confirm booking without explicit user confirmation

INTENT TYPES:
1. search - Test or symptom search
2. filter - Price/rating/location filters
3. add_to_cart - Add specific test from specific lab
4. remove_from_cart - Remove test from cart
5. view_cart - Show cart contents
6. availability - Check slots (requires non-empty cart)
7. booking - Confirm booking (requires cart + collection_method + slot)
8. post_booking - Reschedule/cancel/reports
9. chat - Clarifications, questions, interruptions

SYMPTOM → TEST MAPPING:
- Fatigue/Tiredness → ["Complete Blood Count (CBC)", "Thyroid Function Test", "Vitamin D Test"]
- Fever/Infection → ["Complete Blood Count (CBC)"]
- Diabetes → ["HbA1c", "Fasting Blood Sugar"]
- Thyroid → ["Thyroid Function Test"]

JOURNEY ENFORCEMENT:
- search → Sets journey_step = discovery
- Cart operations allowed only after discovery
- availability requires non-empty cart
- booking requires: cart + collection_method + selected_slot

INTERRUPTION HANDLING:
- Mid-journey questions (e.g., "What is CBC?") → chat response, restore journey_step
- User can ask clarifications at any point

OUTPUT STRUCTURE:
{
  "type": "search | filter | add_to_cart | remove_from_cart | view_cart | availability | booking | chat",
  "query": "test name OR list of test names",
  "filters": {"max_price": <number>, "home_collection": <boolean>, "lab_name": "string"},
  "test_id": "test_xxx",
  "lab_id": "lab_xxx",
  "response": "string (only for chat)"
}

EXAMPLES:

User: "I need CBC test"
Output: {"type": "search", "query": "Complete Blood Count (CBC)", "filters": {}}

User: "I feel tired"
Output: {"type": "search", "query": ["Complete Blood Count (CBC)", "Thyroid Function Test", "Vitamin D Test"], "filters": {}}

User: (after seeing labs) "add Ruby Hall CBC"
Output: {"type": "add_to_cart", "test_id": "test_blood_001", "lab_id": "lab_001"}

User: "show my cart"
Output: {"type": "view_cart"}

User: "remove thyroid test"
Output: {"type": "remove_from_cart", "test_id": "test_blood_003"}

User: (during cart) "what is HbA1c test?"
Output: {"type": "chat", "response": "HbA1c measures average blood sugar levels over 2-3 months. It's the gold standard for diabetes monitoring. No fasting required."}

User: "book my tests"
Output: {"type": "availability"}

User: "proceed to book"
Output: {"type": "availability"}

User: "what are the slots"
Output: {"type": "availability"}

User: "show available slots"
Output: {"type": "availability"}

User: "when can I book"
Output: {"type": "availability"}

User: "yes" (after being asked about booking)
Output: {"type": "availability"}

User: "cheapest CBC"
Output: {"type": "search", "query": "Complete Blood Count (CBC)", "filters": {"sort_by": "price_asc"}}
"""
        
        user_prompt = f"""
        {state_text}
        
        Conversation History:
        {history_text}
        
        Current User Query: "{user_query}"
        
        JSON Output:
        """

        try:
            completion = self.client.chat.completions.create(
                model=self.lab_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                top_p=0.7,
                max_tokens=256
            )
            text = completion.choices[0].message.content.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                text = text.rsplit("\n```", 1)[0]
            return json.loads(text)
        except Exception as e:
            print(f"LLM Lab Test Parsing Error: {e}")
            return {"type": "search", "query": user_query, "filters": {}}
