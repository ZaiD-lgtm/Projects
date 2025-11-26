import random
from datetime import datetime, timedelta, timezone


def generate_random_iso_times(n_times, min_gap_minutes=45, max_gap_minutes=120):
    if n_times <= 0:
        return []
    # gap greater than max
    if min_gap_minutes > max_gap_minutes:
        print("Warning: min_gap_minutes cannot be greater than max_gap_minutes. Swapping values.")
        min_gap_minutes, max_gap_minutes = max_gap_minutes, min_gap_minutes

    scheduled_times = []

    current_utc_time = datetime.now(timezone.utc)

    next_schedule_time = current_utc_time + timedelta(minutes=min_gap_minutes)

    for _ in range(n_times):
        scheduled_times.append(next_schedule_time.strftime('%Y-%m-%dT%H:%M:%SZ'))

        random_gap_seconds = random.randint(min_gap_minutes * 60, max_gap_minutes * 60)
        next_schedule_time += timedelta(seconds=random_gap_seconds)

    return scheduled_times


if __name__ == "__main__":
    print("Generating 5 random ISO times with gaps between 30 minutes and 2 hours:")
    times = generate_random_iso_times(10)
    for i, t in enumerate(times):
        print(f"Time {i + 1}: {t}")
