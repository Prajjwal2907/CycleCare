from datetime import datetime, date


def normalize_sleep_payload(item, provider='generic'):
    """
    Normalizes a sleep payload dictionary into:
    {
        'date': 'YYYY-MM-DD',
        'total_sleep_minutes': int,
        'deep_sleep_minutes': int,
        'rem_sleep_minutes': int,
        'light_sleep_minutes': int,
        'source_provider': str
    }
    """
    raw_date = item.get('date')
    if isinstance(raw_date, (datetime, date)):
        date_str = str(raw_date)
    else:
        date_str = str(raw_date).split('T')[0] if raw_date else str(date.today())

    total_m = item.get('total_sleep_minutes')
    if total_m is None and 'total_sleep_seconds' in item:
        total_m = item['total_sleep_seconds'] // 60
    elif total_m is None and 'duration_minutes' in item:
        total_m = item['duration_minutes']
    total_m = int(total_m) if total_m is not None else 0

    deep_m = item.get('deep_sleep_minutes')
    if deep_m is None and 'deep_sleep_seconds' in item:
        deep_m = item['deep_sleep_seconds'] // 60
    deep_m = int(deep_m) if deep_m is not None else 0

    rem_m = int(item.get('rem_sleep_minutes') or item.get('rem_sleep_seconds', 0) // 60 or 0)
    light_m = int(item.get('light_sleep_minutes') or item.get('light_sleep_seconds', 0) // 60 or 0)

    return {
        'date': date_str,
        'total_sleep_minutes': total_m,
        'deep_sleep_minutes': deep_m,
        'rem_sleep_minutes': rem_m,
        'light_sleep_minutes': light_m,
        'source_provider': provider,
    }


def normalize_exercise_payload(item, provider='generic'):
    """
    Normalizes an exercise payload dictionary into:
    {
        'date': 'YYYY-MM-DD',
        'activity_type': str,
        'duration_minutes': int,
        'intensity': 'low' | 'medium' | 'high',
        'calories_burned': int | None,
        'source_provider': str
    }
    """
    raw_date = item.get('date')
    date_str = str(raw_date).split('T')[0] if raw_date else str(date.today())

    intensity = str(item.get('intensity', 'medium')).lower()
    if intensity not in ('low', 'medium', 'high'):
        intensity = 'medium'

    duration_m = int(item.get('duration_minutes') or item.get('duration_seconds', 0) // 60 or 0)
    calories = item.get('calories_burned') or item.get('calories')
    calories_int = int(calories) if calories is not None else None

    return {
        'date': date_str,
        'activity_type': str(item.get('activity_type') or item.get('type') or 'workout').lower(),
        'duration_minutes': duration_m,
        'intensity': intensity,
        'calories_burned': calories_int,
        'source_provider': provider,
    }


def normalize_alcohol_payload(item, provider='generic'):
    """
    Normalizes an alcohol signal payload into:
    {
        'timestamp': datetime or ISO string,
        'confidence_score': float,
        'is_estimated': bool,
        'notes': str,
        'signal_source': str
    }
    """
    timestamp = item.get('timestamp') or item.get('time')
    confidence = float(item.get('confidence_score') or item.get('confidence') or 0.0)
    is_estimated = item.get('is_estimated', True)
    notes = item.get('notes', '')

    return {
        'timestamp': timestamp,
        'confidence_score': confidence,
        'is_estimated': is_estimated,
        'notes': notes,
        'signal_source': f"{provider}_vitals",
    }
