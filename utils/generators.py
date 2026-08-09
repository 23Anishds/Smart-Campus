import random
import datetime
from typing import Generator, Dict, Any

def generate_attendance_heatmap(class_id: int, weeks: int = 4) -> Generator[Dict[str, Any], None, None]:
    """
    Generates dummy attendance heatmap data week-by-week (Concept #3 - Generators).
    Yields one week of data at a time to represent memory-efficient streaming.
    """
    today = datetime.datetime.now()
    start_date = today - datetime.timedelta(days=today.weekday() + (weeks*7))
    
    for w in range(weeks):
        week_data = []
        for i in range(5):  # Mon-Fri
            current_day = start_date + datetime.timedelta(days=(w*7) + i)
            # Simulated data: [day_index, period_index, attendance_value]
            for period in range(6): # 6 periods a day
                 # Slightly lower attendance on fridays (i==4) and later periods
                value = random.randint(70, 100) if i < 4 else random.randint(50, 90)
                week_data.append({
                    "date": current_day.strftime("%Y-%m-%d"),
                    "day_index": i,
                    "period_index": period,
                    "attendance": value
                })
        yield {"week": w+1, "data": week_data}

def generate_performance_trend(student_id: int, days: int = 30) -> Generator[Dict[str, Any], None, None]:
    """
    Generates simulated daily performance scores (Concept #3).
    """
    today = datetime.datetime.now()
    base_score = random.uniform(70.0, 95.0)  # Random base score
    
    for i in range(days):
        current_day = today - datetime.timedelta(days=days - i)
        # Random walk for trend
        change = random.uniform(-2.0, 2.0)
        base_score = max(0.0, min(100.0, base_score + change))
        yield {
            "date": current_day.strftime("%Y-%m-%d"),
            "score": round(base_score, 1)
        }
