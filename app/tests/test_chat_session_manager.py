import json
from app.services.query_parameters import QueryParameters

def test_get_or_create_creates(session_mgr):
    sid = session_mgr.get_or_create(None)
    assert session_mgr.r.exists(sid)

def test_add_and_load_messages(session_mgr):
    sid = session_mgr.get_or_create(None)
    session_mgr.add_message(sid, "user", "hello")
    history = session_mgr._load(sid)
    assert history[-1]["content"] == "hello"

def test_record_query(session_mgr):
    sid = session_mgr.get_or_create(None)
    qp = QueryParameters({"budget":"1","size":"2","type":"3","city":"4"})
    session_mgr.record_query(sid, qp)
    stored = session_mgr.get_queries(sid)
    assert stored == [qp.to_dict()]
