"""
MongoDB Handler - manages all log persistence operations.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from pymongo import MongoClient, DESCENDING
from pymongo.errors import ConnectionFailure
from constants import MONGO_URI, MONGO_DB, LOGS_COLLECTION
from datetime import datetime, timezone, timedelta

_client = None
_db     = None


def get_db():
    global _client, _db
    if _db is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        _db     = _client[MONGO_DB]
        # Ensure indexes
        _db[LOGS_COLLECTION].create_index([("trace_id", 1)])
        _db[LOGS_COLLECTION].create_index([("service_name", 1)])
        _db[LOGS_COLLECTION].create_index([("status", 1)])
        _db[LOGS_COLLECTION].create_index([("timestamp", DESCENDING)])
    return _db


def insert_log(log_doc: dict):
    db = get_db()
    db[LOGS_COLLECTION].insert_one(log_doc)
    log_doc.pop("_id", None)
    return log_doc


def get_logs(limit=100, service=None, status=None, trace_id=None):
    db    = get_db()
    query = {}
    if service:   query["service_name"] = service
    if status:    query["status"]       = status.upper()
    if trace_id:  query["trace_id"]     = {"$regex": trace_id, "$options": "i"}

    cursor = db[LOGS_COLLECTION].find(
        query, {"_id": 0}
    ).sort("timestamp", DESCENDING).limit(limit)
    return list(cursor)


def get_logs_by_trace(trace_id: str):
    db = get_db()
    return list(
        db[LOGS_COLLECTION]
        .find({"trace_id": trace_id}, {"_id": 0})
        .sort("timestamp", 1)
    )


def get_total_count():
    return get_db()[LOGS_COLLECTION].count_documents({})


def get_error_count():
    return get_db()[LOGS_COLLECTION].count_documents({"status": "ERROR"})


def get_stats_by_service():
    db = get_db()
    pipeline = [
        {"$group": {
            "_id": "$service_name",
            "total":    {"$sum": 1},
            "errors":   {"$sum": {"$cond": [{"$eq": ["$status", "ERROR"]}, 1, 0]}},
            "avg_resp": {"$avg": "$response_time"}
        }},
        {"$sort": {"total": -1}}
    ]
    return list(db[LOGS_COLLECTION].aggregate(pipeline))


def get_recent_errors(limit=20):
    return get_logs(limit=limit, status="ERROR")


def get_hourly_counts(hours=24):
    """Return request counts per hour for the last N hours."""
    db    = get_db()
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    pipeline = [
        {"$match": {"timestamp": {"$gte": since.isoformat()}}},
        {"$group": {
            "_id": {
                "$substr": ["$timestamp", 0, 13]   # YYYY-MM-DDTHH
            },
            "count": {"$sum": 1},
            "errors": {"$sum": {"$cond": [{"$eq": ["$status", "ERROR"]}, 1, 0]}}
        }},
        {"$sort": {"_id": 1}}
    ]
    return list(db[LOGS_COLLECTION].aggregate(pipeline))


def get_distinct_traces():
    return get_db()[LOGS_COLLECTION].distinct("trace_id")
