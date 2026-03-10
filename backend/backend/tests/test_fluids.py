def test_get_fluids(client):
    response = client.get("/api/fluids")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Check that known fluids are present
    for fluid in ["Methane", "Nitrogen", "Oxygen", "Water"]:
        assert fluid in data
    # Check the list is sorted
    assert data == sorted(data)


def test_get_units(client):
    response = client.get("/api/units")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    # Check known keys exist
    for key in ["flow_v", "suction_pressure", "suction_temperature", "head", "power"]:
        assert key in data
    # Check structure of an entry
    entry = data["suction_pressure"]
    assert "label" in entry
    assert "units" in entry
    assert isinstance(entry["units"], list)
