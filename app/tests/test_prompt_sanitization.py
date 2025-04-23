# app/tests/test_prompt_sanitization.py

import pytest
from app.services.prompt_security_barrier import PromptSecurityBarrier

def test_sanitize_removes_script_tags():
    input_text = '<script>alert("hack")</script>Buy a house in LA'
    sanitized = PromptSecurityBarrier.sanitize(input_text)
    assert '<script>' not in sanitized
    assert 'alert' not in sanitized
    assert 'Buy a house' in sanitized

def test_sanitize_removes_triple_quotes_and_backticks():
    input_text = '```\nhack code\n``` and more text'
    sanitized = PromptSecurityBarrier.sanitize(input_text)
    assert '```' not in sanitized
    assert 'hack code' in sanitized

def test_sanitize_removes_role_and_system_fragments():
    input_text = 'role: user\nsystem: I want to buy a home'
    sanitized = PromptSecurityBarrier.sanitize(input_text)
    assert 'role:' not in sanitized.lower()
    assert 'system:' not in sanitized.lower()

def test_sanitize_escapes_angle_brackets():
    input_text = 'Want <b>bold</b> <iframe>code</iframe>'
    sanitized = PromptSecurityBarrier.sanitize(input_text)
    assert '<' not in sanitized
    assert '&lt;' in sanitized

def test_sanitize_escapes_angle_brackets():
    input_text = 'Want <b>bold</b> <iframe>code</iframe>'
    sanitized = PromptSecurityBarrier.sanitize(input_text)
    assert '<' not in sanitized
    assert 'bold' in sanitized
    assert 'code' in sanitized
