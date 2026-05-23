"""
Alert Engine - detects failure patterns and generates alerts.
"""
from mongo_handler import get_db
from constants import LOGS_COLLECTION
from datetime import datetime, timezone, timedelta

ALERT_THRESHOLD_ERRORS = 5      # alert if a service has >= 5 errors in last 5 minutes
ALERT_WINDOW_MINUTES   = 5


def get_active_alerts():
    """
    Scan recent logs and return any triggered alerts.
    """
    db    = get_db()
    since = datetime.now(timezone.utc) - timedelta(minutes=ALERT_WINDOW_MINUTES)

    pipeline = [
        {"$match": {
            "status":    "ERROR",
            "timestamp": {"$gte": since.isoformat()}
        }},
        {"$group": {
            "_id":   "$service_name",
            "count": {"$sum": 1},
            "last":  {"$max": "$timestamp"},
            "msgs":  {"$push": "$message"}
        }},
        {"$match": {"count": {"$gte": ALERT_THRESHOLD_ERRORS}}},
        {"$sort":  {"count": -1}}
    ]

    rows   = list(db[LOGS_COLLECTION].aggregate(pipeline))
    alerts = []
    for row in rows:
        alerts.append({
            "service":     row["_id"],
            "error_count": row["count"],
            "last_error":  row["last"],
            "severity":    "CRITICAL" if row["count"] >= 10 else "WARNING",
            "message":     f"{row['_id']} had {row['count']} errors in the last {ALERT_WINDOW_MINUTES} minutes",
            "sample_errors": row["msgs"][-3:],
        })
    return alerts
