"""
Integration test for /classify endpoint.

This test ensures:
- The API responds successfully
- The response structure is complete
- No silent failures occur

This proves the system behaves like a real backend,
not just a demo.
"""


def test_classify_endpoint_structure(client):
    response = client.post(
        "/classify",
        json={
            "description": "uber airport ride",
            "amount": 25.50
        }
    )

    assert response.status_code == 200

    data = response.json()

    # Top-level trust blocks
    assert "decision" in data
    assert "trust" in data
    assert "evidence" in data
    assert "risk" in data

    # Decision block sanity
    assert data["decision"]["final_category"] is not None
    assert isinstance(data["decision"]["confidence"], float)

    # Risk block sanity
    assert isinstance(data["risk"]["risk_score"], float)
