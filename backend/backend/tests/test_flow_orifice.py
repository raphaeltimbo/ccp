def test_calculate_flow_orifice(client):
    response = client.post(
        "/api/flow-orifice/calculate",
        json={
            "upstream_pressure": {"magnitude": 10, "unit": "bar"},
            "upstream_temperature": {"magnitude": 300, "unit": "degK"},
            "fluid": {"components": {"nitrogen": 1.0}},
            "pressure_drop": {"magnitude": 0.5, "unit": "bar"},
            "D": {"magnitude": 0.3, "unit": "m"},
            "d": {"magnitude": 0.15, "unit": "m"},
            "tappings": "flange",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "flow_m" in data
    assert "flow_v" in data
    assert data["flow_m"]["magnitude"] > 0
    assert data["flow_v"]["magnitude"] > 0
