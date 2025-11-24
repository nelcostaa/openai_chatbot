#!/usr/bin/env python3
"""
Test script to reproduce "Next Chapter" button bug.
Expected: AI acknowledges phase transition ("Great, we finished CHILDHOOD...")
Actual: AI continues with old phase prompts
"""

import json

import requests

# Simulate conversation flow leading up to "Next Chapter" click
BASE_URL = "http://localhost:5000/api/chat"

# Step 1: Initial greeting
messages_greeting = [
    {
        "role": "assistant",
        "content": "Welcome! I'm here to help you tell your life story chronologically...",
    }
]

# Step 2: User says yes
messages_yes = [
    {
        "role": "assistant",
        "content": "Welcome! I'm here to help you tell your life story chronologically...",
    },
    {"role": "user", "content": "yes"},
    {"role": "assistant", "content": "To customize the interview..."},
]

# Step 3: User selects age (via button, simulating the API call)
print("=" * 80)
print("STEP 1: Simulating age selection (button click)")
print("=" * 80)

age_selection_payload = {
    "messages": messages_yes,
    "route": "1",
    "phase": "AGE_SELECTION",
    "age_range": None,
    "age_selection_input": "4",  # Ages 46-60
    "selected_tags": [],
}

response = requests.post(BASE_URL, json=age_selection_payload)
print(f"Status: {response.status_code}")
age_result = response.json()
print(f"Phase after age selection: {age_result.get('phase')}")
print(f"Response (should be empty): '{age_result.get('response')}'")
print()

# Step 4: Get CHILDHOOD opening prompt
print("=" * 80)
print("STEP 2: Getting CHILDHOOD opening prompt")
print("=" * 80)

childhood_opening_payload = {
    "messages": messages_yes,
    "route": "1",
    "phase": "CHILDHOOD",
    "age_range": "46_60",
    "selected_tags": [],
}

response = requests.post(BASE_URL, json=childhood_opening_payload)
childhood_result = response.json()
print(f"Phase: {childhood_result.get('phase')}")
print(f"CHILDHOOD Opening: {childhood_result.get('response')[:100]}...")
print()

# Step 5: User shares childhood memory
messages_with_childhood = messages_yes + [
    {"role": "assistant", "content": childhood_result.get("response")},
    {
        "role": "user",
        "content": "I grew up in a small town. My fondest memory is playing in the fields with my siblings.",
    },
]

# Step 6: AI asks follow-up
followup_payload = {
    "messages": messages_with_childhood,
    "route": "1",
    "phase": "CHILDHOOD",
    "age_range": "46_60",
    "selected_tags": [],
}

response = requests.post(BASE_URL, json=followup_payload)
followup_result = response.json()
messages_with_followup = messages_with_childhood + [
    {"role": "assistant", "content": followup_result.get("response")}
]
print("=" * 80)
print("STEP 3: AI Follow-up in CHILDHOOD")
print("=" * 80)
print(f"AI: {followup_result.get('response')[:100]}...")
print()

# Step 7: NOW THE BUG - User clicks "Next Chapter" button
print("=" * 80)
print("🐛 STEP 4: USER CLICKS 'Next Chapter' BUTTON (THE BUG)")
print("=" * 80)
print(
    "Expected: AI says 'Great, we finished CHILDHOOD. Now let's talk about your ADOLESCENCE...'"
)
print("Actual bug: AI continues with CHILDHOOD prompts")
print()

next_chapter_payload = {
    "messages": messages_with_followup,  # All messages so far (no new user message)
    "route": "1",
    "phase": "CHILDHOOD",  # Frontend sends current phase before advancement
    "age_range": "46_60",
    "advance_phase": True,  # THIS IS THE SIGNAL
    "selected_tags": [],
}

response = requests.post(BASE_URL, json=next_chapter_payload)
next_chapter_result = response.json()

print(f"Response phase: {next_chapter_result.get('phase')}")
print(f"Response model: {next_chapter_result.get('model')}")
print()
print("AI Response:")
print("-" * 80)
print(next_chapter_result.get("response"))
print("-" * 80)
print()

# Analysis
response_text = next_chapter_result.get("response", "").lower()
if "adolescence" in response_text and (
    "finished" in response_text
    or "completed" in response_text
    or "great" in response_text
):
    print("✅ SUCCESS: AI acknowledged phase transition!")
elif "childhood" in response_text:
    print(
        "❌ BUG CONFIRMED: AI is still talking about CHILDHOOD instead of acknowledging transition to ADOLESCENCE"
    )
elif "adolescence" in response_text:
    print(
        "⚠️ PARTIAL: AI mentions ADOLESCENCE but might not have proper transition message"
    )
else:
    print("⚠️ UNCLEAR: Response doesn't clearly indicate phase")
