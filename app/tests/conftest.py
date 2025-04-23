import pytest, fakeredis
from app.services.chat_session_manager import ChatSessionManager

@pytest.fixture
def redis_fake():
    return fakeredis.FakeStrictRedis(decode_responses=True)

@pytest.fixture
def session_mgr(redis_fake):
    return ChatSessionManager(redis_fake)
