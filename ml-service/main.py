from datetime import date
from pathlib import Path
from statistics import mean
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(
    title="CycleCare ML Service",
    version="1.0.0",
    description="CycleCare ML service for privacy-preserving cycle, alcohol screening, craving, and suggestion workflows.",
)

MODEL_PATH = Path(__file__).resolve().parent / "artifacts" / "alcohol_use_classifier.joblib"
_alcohol_model = None


class CravingPayload(BaseModel):
    craving: str = Field(min_length=1, max_length=255)
    dietary_preference: str = "vegetarian"
    vegetarian_days: list[str] = []


class CyclePayload(BaseModel):
    cycles: list[dict[str, Any]] = []


class SuggestionPayload(BaseModel):
    patient_id: int | None = None
    dietary_preference: str = "vegetarian"
    cycles: list[dict[str, Any]] = []
    sleep: list[dict[str, Any]] = []
    exercise: list[dict[str, Any]] = []
    nutrition: list[dict[str, Any]] = []
    alcohol: dict[str, Any] = {}


@app.get("/health/")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "ml-service",
        "alcohol_model": "ready" if MODEL_PATH.exists() else "not_trained",
    }


class AlcoholPredictionPayload(BaseModel):
    features: dict[str, Any] = {}


@app.post("/api/v1/predict-alcohol/")
def predict_alcohol(payload: AlcoholPredictionPayload) -> dict[str, Any]:
    """Return a screening probability from non-identifying health features."""
    global _alcohol_model
    if _alcohol_model is None:
        if not MODEL_PATH.exists():
            return {
                "status": "unavailable",
                "reason": "The research model has not been trained yet.",
                "diagnostic": False,
            }
        import joblib
        _alcohol_model = joblib.load(MODEL_PATH)["pipeline"]

    import pandas as pd
    features = pd.DataFrame([payload.features])
    probability = float(_alcohol_model.predict_proba(features)[0, 1])
    return {
        "status": "screening_signal",
        "probability": round(probability, 4),
        "signal": probability >= 0.5,
        "diagnostic": False,
        "message": "This is a research screening signal and requires clinician review.",
    }


@app.post("/api/v1/craving-alternative/")
def craving_alternative(payload: CravingPayload) -> dict[str, Any]:
    craving = payload.craving.lower().strip()
    vegetarian = payload.dietary_preference in {"vegetarian", "non_veg_with_veg_days"}

    if "pizza" in craving:
        return {
            "name": "Cauliflower Crust Veggie Pizza",
            "description": "A lighter take on pizza loaded with bell peppers, onions, and part-skim mozzarella.",
            "dietTag": "Vegetarian Friendly",
            "calories": 280,
            "protein_g": 14.0,
        }
    if "chocolate" in craving:
        return {
            "name": "Dark Chocolate Energy Bites",
            "description": "Rolled oats, almond butter, and 70% dark chocolate chips rolled into satisfying bites.",
            "dietTag": "Vegan",
            "calories": 180,
            "protein_g": 5.5,
        }
    if "fries" in craving:
        return {
            "name": "Baked Sweet Potato Fries",
            "description": "Wedges of sweet potato tossed lightly in olive oil and smoked paprika, baked crisp.",
            "dietTag": "Vegan & Gluten-Free",
            "calories": 210,
            "protein_g": 3.0,
        }
    if "burger" in craving:
        patty = "Grilled Paneer & Veggie" if vegetarian else "Grilled Lean Chicken"
        return {
            "name": f"{patty} Burger",
            "description": "A whole grain bun with a protein-rich patty, baby spinach, tomato, and yogurt herb sauce.",
            "dietTag": "High Protein",
            "calories": 360,
            "protein_g": 26.0,
        }
    return {
        "name": "Nutrient-Dense Power Bowl",
        "description": "A balanced bowl of quinoa, fresh greens, roasted chickpeas or paneer, and a tahini drizzle.",
        "dietTag": "Balanced Meal",
        "calories": 320,
        "protein_g": 16.0,
    }


@app.post("/api/v1/predict-cycle/")
def predict_cycle(payload: CyclePayload) -> dict[str, Any]:
    starts: list[date] = []
    for cycle in payload.cycles:
        value = cycle.get("start_date")
        if not value:
            continue
        try:
            starts.append(date.fromisoformat(str(value)[:10]))
        except ValueError:
            continue

    starts.sort()
    gaps = [(later - earlier).days for earlier, later in zip(starts, starts[1:]) if later > earlier]
    predicted_gap = round(mean(gaps)) if gaps else 28
    return {
        "predicted_gap_days": predicted_gap,
        "confidence": min(0.95, 0.5 + len(gaps) * 0.1),
        "model": "rolling_average_development",
    }


@app.post("/api/v1/generate-suggestions/")
def generate_suggestions(payload: SuggestionPayload) -> list[dict[str, str]]:
    suggestions = [
        {"category": "hydration", "text": "Aim for regular water intake throughout the day to support hydration."},
        {"category": "diet", "text": "Include a fiber-rich complex carbohydrate and a protein source in your next meal."},
    ]
    if payload.sleep and all((item.get("total_sleep_minutes") or 0) < 420 for item in payload.sleep[:3]):
        suggestions.append({"category": "lifestyle", "text": "Your recent sleep entries look short; protect a consistent wind-down routine tonight."})
    if payload.exercise and not any((item.get("duration_minutes") or 0) >= 20 for item in payload.exercise[:3]):
        suggestions.append({"category": "exercise", "text": "Consider a gentle 20-minute walk or stretch session if it feels comfortable."})
    if (payload.alcohol.get("signals_tracked") or 0) > 0:
        suggestions.append({"category": "lifestyle", "text": "A clinician should review the recent alcohol-related health signal before offering personalized guidance."})
    return suggestions
