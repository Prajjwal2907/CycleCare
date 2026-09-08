from datetime import timedelta
from django.utils import timezone
from core.ml_client import ml_client
from .models import CycleEntry


def calculate_cycle_metrics(patient_profile):
    """
    Computes historical statistics and predicts the next cycle gap and start date.
    Uses rolling averages over past cycles with a clean seam to call ml-service.
    """
    entries = list(CycleEntry.objects.filter(patient=patient_profile).order_by('start_date'))
    today = timezone.now().date()

    if not entries:
        return {
            "total_entries": 0,
            "average_duration_days": 0.0,
            "average_gap_days": 28.0,
            "predicted_next_cycle_gap": 28,
            "predicted_next_start_date": None,
            "days_until_next_cycle": None,
            "symptom_frequency": {},
            "flow_distribution": {},
        }

    # 1. Average period duration (bleeding length)
    durations = [e.cycle_duration for e in entries if e.cycle_duration > 0]
    avg_duration = round(sum(durations) / len(durations), 1) if durations else 0.0

    # 2. Cycle-to-cycle interval gaps (start date of cycle i+1 minus start date of cycle i)
    gaps = []
    for i in range(1, len(entries)):
        gap = (entries[i].start_date - entries[i - 1].start_date).days
        if gap > 0:
            gaps.append(gap)

    if gaps:
        avg_gap = round(sum(gaps) / len(gaps), 1)
        predicted_gap = int(round(avg_gap))
    else:
        avg_gap = 28.0
        predicted_gap = 28

    latest_entry = entries[-1]
    predicted_next_start = latest_entry.start_date + timedelta(days=predicted_gap)
    days_until_next = (predicted_next_start - today).days

    # Clean seam: Attempt ML-service enhancement if available
    try:
        if len(entries) >= 2:
            formatted_history = [
                {"start_date": str(e.start_date), "end_date": str(e.end_date), "duration": e.cycle_duration}
                for e in entries[-6:]
            ]
            ml_pred = ml_client.predict_cycle(formatted_history)
            if ml_pred and "predicted_gap_days" in ml_pred:
                predicted_gap = int(ml_pred["predicted_gap_days"])
                predicted_next_start = latest_entry.start_date + timedelta(days=predicted_gap)
                days_until_next = (predicted_next_start - today).days
    except Exception:
        pass  # Gracefully fall back to rolling average calculation

    # 3. Symptom frequency breakdown
    symptom_freq = {}
    for entry in entries:
        if isinstance(entry.symptoms, list):
            for sym in entry.symptoms:
                sym_str = str(sym).strip().lower()
                symptom_freq[sym_str] = symptom_freq.get(sym_str, 0) + 1

    # 4. Flow distribution breakdown
    flow_dist = {}
    for entry in entries:
        flow_dist[entry.flow_intensity] = flow_dist.get(entry.flow_intensity, 0) + 1

    return {
        "total_entries": len(entries),
        "average_duration_days": avg_duration,
        "average_gap_days": avg_gap,
        "predicted_next_cycle_gap": predicted_gap,
        "predicted_next_start_date": predicted_next_start,
        "days_until_next_cycle": max(0, days_until_next) if days_until_next is not None else None,
        "symptom_frequency": symptom_freq,
        "flow_distribution": flow_dist,
    }
