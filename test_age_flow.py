#!/usr/bin/env python3
"""
Test to reproduce age selection bug - checking phase advancement flow.
"""

from api.routes.chronological_steward import ChronologicalSteward

# Simulate the exact flow
route = ChronologicalSteward()

print("=== INITIAL STATE ===")
print(f"Phase: {route.phase}")
print(f"Phase order: {route.phase_order}")
print(f"Age range: {route.age_range}")
print()

# Step 1: User says "yes" to greeting
print("=== STEP 1: User says 'yes' ===")
route.add_message("user", "yes")
if route.should_advance("yes", explicit_transition=False):
    route.phase = route.advance_phase()
    print(f"Advanced to: {route.phase}")
print(f"Phase order: {route.phase_order}")
print()

# Step 2: Age selection (simulating age_selection_input='2' for 18-30)
print("=== STEP 2: Age selection via metadata (age_selection_input='2') ===")
# Frontend sends age_selection_input='2', backend processes:
if route.should_advance("2", explicit_transition=False):
    route.phase = route.advance_phase()
    print(f"Advanced to: {route.phase}")
    print(f"Age range: {route.age_range}")
    print(f"Phase order: {route.phase_order}")
print()

# Step 3: Get system instruction for CHILDHOOD
print("=== STEP 3: Get CHILDHOOD system instruction ===")
try:
    phase_config = route.get_current_phase()
    print(f"Current phase: {route.phase}")
    print(f"System instruction preview:")
    print(phase_config["system_instruction"][:200] + "...")
except Exception as e:
    print(f"ERROR: {e}")
print()

# Step 4: Check if AGE_SELECTION is still in phase_order
print("=== STEP 4: Verify phase_order contents ===")
print(f"Phase order: {route.phase_order}")
print(f"AGE_SELECTION in phase_order: {'AGE_SELECTION' in route.phase_order}")
print()

# Step 5: What happens if we accidentally get AGE_SELECTION system instruction?
print("=== STEP 5: What if AGE_SELECTION instruction is retrieved? ===")
age_instruction = route.PHASES["AGE_SELECTION"]["system_instruction"]
print("AGE_SELECTION instruction preview:")
print(age_instruction[:200] + "...")
