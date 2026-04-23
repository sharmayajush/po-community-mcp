import json
import os
from typing import Annotated

from pydantic import Field

# ── DB Path Configuration ──────────────────────────────────────────────────────
# LOCAL: Uses relative path from this file to the shared data/ folder.
# PRODUCTION: Set the HR_DB_PATH environment variable to an absolute path.
# Example: HR_DB_PATH=/app/data/mock_hr_db.json
_DEFAULT_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/mock_hr_db.json"))
DB_PATH = os.getenv("HR_DB_PATH", _DEFAULT_DB_PATH)


async def search_available_clinicians(
    specialty: Annotated[
        str,
        Field(description="The medical specialty required (e.g. 'Cardiology', 'Neurology', 'Trauma Surgery')"),
    ]
) -> str:
    """Searches the hospital HR database for an available clinician matching the required specialty."""

    try:
        with open(DB_PATH, "r") as f:
            db_data = json.load(f)

        clinicians = db_data.get("clinicians", [])

        matches = []
        for clinician in clinicians:
            # We strictly check for 'Available' status and a matching specialty
            if clinician.get("status") == "Available" and clinician.get("specialty", "").lower() == specialty.lower():
                matches.append(clinician)

        if not matches:
            # NOTE: We return the error as a normal string so the LLM can reason about it.
            # Do NOT use create_text_response(is_error=True) — that raises a ValueError and crashes the server.
            return f"No available clinicians found right now for specialty: {specialty}. They might be in surgery."

        # Format the response clearly for the LLM
        response_text = f"Found {len(matches)} available clinician(s) for {specialty}:\n\n"
        for idx, match in enumerate(matches, 1):
            response_text += f"{idx}. {match['name']} (ID: {match['id']})\n"
            response_text += f"   Location: {match['location']}\n"
            response_text += f"   Current Patient Load: {match['current_patient_load']}\n"

        return response_text

    except FileNotFoundError:
        return f"Critical Error: The HR database file could not be found at: {DB_PATH}"
    except Exception as e:
        return f"Database Error: {str(e)}"
