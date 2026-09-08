import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class MLServiceError(Exception):
    """Base exception for ML service communication failures."""
    pass


class MLServiceTimeoutError(MLServiceError):
    """Raised when the ML service takes too long to respond."""
    pass


class MLServiceClient:
    """
    Client interface for external FastAPI ml-service endpoints.
    Handles timeouts, connection failures, and provides fallback behavior.
    """

    def __init__(self, base_url=None, timeout=6):
        self.base_url = (base_url or getattr(settings, 'ML_SERVICE_URL', 'http://localhost:8001')).rstrip('/')
        self.timeout = timeout

    def get_craving_alternative(self, craving_text, dietary_preference="vegetarian", vegetarian_days=None):
        """
        Calls POST /api/v1/craving-alternative/ on ml-service.
        Returns a healthier alternative respecting dietary preferences.
        """
        endpoint = f"{self.base_url}/api/v1/craving-alternative/"
        payload = {
            "craving": craving_text,
            "dietary_preference": dietary_preference,
            "vegetarian_days": vegetarian_days or []
        }
        try:
            response = requests.post(endpoint, json=payload, timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"ML Service craving returned {response.status_code}: {response.text}")
                raise MLServiceError(f"ML service returned status {response.status_code}")

        except requests.Timeout as e:
            logger.warning(f"Timeout connecting to ML service at {endpoint}: {e}")
            raise MLServiceTimeoutError("ML service timed out while finding a healthy alternative.")
        except requests.RequestException as e:
            logger.warning(f"Connection error to ML service at {endpoint}: {e}")
            # Rule-based fallback matching app/www/craving.js specification
            return self._fallback_craving(craving_text, dietary_preference)

    def generate_suggestions(self, patient_data):
        """
        Calls POST /api/v1/generate-suggestions/ on ml-service.
        Passes recent health metrics to generate tailored lifestyle suggestions.
        """
        endpoint = f"{self.base_url}/api/v1/generate-suggestions/"
        try:
            response = requests.post(endpoint, json=patient_data, timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"ML Service suggestions returned {response.status_code}: {response.text}")
                raise MLServiceError(f"ML service returned status {response.status_code}")

        except requests.Timeout as e:
            logger.warning(f"Timeout connecting to ML service at {endpoint}: {e}")
            raise MLServiceTimeoutError("ML service timed out while generating suggestions.")
        except requests.RequestException as e:
            logger.warning(f"Connection error to ML service at {endpoint}: {e}")
            if settings.DEBUG:
                logger.info("Using fallback suggestions response in DEBUG mode.")
                return [
                    {
                        "category": "hydration",
                        "text": "Aim for 2.5L of water today to support cellular hydration and ease PMS bloating."
                    },
                    {
                        "category": "diet",
                        "text": "Incorporate complex carbohydrates like roasted sweet potato to stabilize insulin spikes."
                    },
                    {
                        "category": "exercise",
                        "text": "Engage in 25 minutes of low-impact walking to support lymphatic drainage and lower cortisol."
                    }
                ]
            raise MLServiceError(f"Unable to reach ML service: {str(e)}")

        def predict_alcohol(self, features):
            """Return a non-diagnostic alcohol screening signal for non-identifying features."""
            endpoint = f"{self.base_url}/api/v1/predict-alcohol/"
            try:
                response = requests.post(endpoint, json={"features": features}, timeout=self.timeout)
                if response.status_code == 200:
                    return response.json()
                raise MLServiceError(f"ML service returned status {response.status_code}")
            except requests.Timeout as error:
                raise MLServiceTimeoutError("ML service timed out during alcohol screening.") from error
            except requests.RequestException as error:
                raise MLServiceError(f"Unable to reach ML service: {error}") from error

    def predict_cycle(self, historical_entries):
        """
        Calls POST /api/v1/predict-cycle/ on ml-service.
        Returns predicted cycle length and next gap in days.
        """
        endpoint = f"{self.base_url}/api/v1/predict-cycle/"
        try:
            response = requests.post(endpoint, json={"cycles": historical_entries}, timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            else:
                raise MLServiceError(f"ML service returned status {response.status_code}")
        except Exception as e:
            logger.warning(f"ML cycle prediction failed or unavailable: {e}")
            # Clean fallback: standard 28-day cycle prediction
            return {"predicted_gap_days": 28, "confidence": 0.5, "model": "rolling_average_fallback"}

    def _fallback_craving(self, craving_text, dietary_preference):
        text = craving_text.lower().strip()
        is_veg = dietary_preference in ('vegetarian', 'non_veg_with_veg_days')

        if "pizza" in text:
            return {
                "name": "Cauliflower Crust Veggie Pizza",
                "description": "A lighter take on pizza loaded with bell peppers, onions, and part-skim mozzarella.",
                "dietTag": "Vegetarian Friendly",
                "calories": 280,
                "protein_g": 14.0
            }
        elif "chocolate" in text:
            return {
                "name": "Dark Chocolate Energy Bites",
                "description": "Rolled oats, almond butter, and 70% dark chocolate chips rolled into satisfying bites.",
                "dietTag": "Vegan",
                "calories": 180,
                "protein_g": 5.5
            }
        elif "fries" in text:
            return {
                "name": "Baked Sweet Potato Fries",
                "description": "Wedges of sweet potato tossed lightly in olive oil and smoked paprika, baked crisp.",
                "dietTag": "Vegan & Gluten-Free",
                "calories": 210,
                "protein_g": 3.0
            }
        elif "burger" in text:
            patty = "Grilled Paneer & Veggie" if is_veg else "Grilled Lean Chicken"
            return {
                "name": f"{patty} Burger",
                "description": "A whole grain bun with a protein-rich patty, baby spinach, tomato, and yogurt herb sauce.",
                "dietTag": "High Protein",
                "calories": 360,
                "protein_g": 26.0
            }
        return {
            "name": "Nutrient-Dense Power Bowl",
            "description": "A balanced bowl of quinoa, fresh greens, roasted chickpeas or paneer, and a tahini drizzle.",
            "dietTag": "Balanced Meal",
            "calories": 320,
            "protein_g": 16.0
        }


# Singleton instance
ml_client = MLServiceClient()
