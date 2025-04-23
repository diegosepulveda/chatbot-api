from app.services.query_parameters import QueryParameters

# Simulated LLM reply that includes a JSON block

def test_complete_query_parsing():
    llm_response = """
        Here's what I found:
        {"budget":"10,000 USD","size":"300 m²","type":"oficina","city":"Guadalajara"}
        Let me know if you'd like to change any criteria.
    """
    params = QueryParameters.from_llm_text(llm_response)

    assert params is not None
    assert params.budget == "10,000 USD"
    assert params.size == "300 m²"
    assert params.type == "oficina"
    assert params.city == "Guadalajara"
    assert params.is_complete() is True

def test_query_url_with_extra_fields():

    llm_response = """
        Got it!
        {"budget":"5000 USD","size":"200 m²","type":"casa","city":"CDMX", "filter1":"pool"}
    """
    params = QueryParameters.from_llm_text(llm_response)

    assert params is not None
    assert params.extra.get("filter1") == "pool"

    url = params.to_query_url()
    assert "budget=5000+USD" in url
    assert "filter1=pool" in url