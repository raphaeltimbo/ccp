def test_straight_through_schema_validation(client):
    """Test that incomplete requests get 422."""
    response = client.post("/api/straight-through/calculate", json={})
    assert response.status_code == 422


def test_straight_through_missing_gas_compositions(client):
    """Test that missing gas_compositions returns 422."""
    response = client.post(
        "/api/straight-through/calculate",
        json={
            "guarantee_gas": "test",
            "data_sheet": {
                "flow": {"magnitude": 100, "unit": "m³/h"},
                "suction_pressure": {"magnitude": 1, "unit": "bar"},
                "suction_temperature": {"magnitude": 300, "unit": "degK"},
                "discharge_pressure": {"magnitude": 5, "unit": "bar"},
                "discharge_temperature": {"magnitude": 400, "unit": "degK"},
                "speed": {"magnitude": 10000, "unit": "rpm"},
                "b": {"magnitude": 28.5, "unit": "mm"},
                "D": {"magnitude": 365, "unit": "mm"},
            },
            "test_points": [],
            "options": {},
        },
    )
    assert response.status_code == 422


def test_straight_through_missing_test_points(client):
    """Test that missing test_points returns 422."""
    response = client.post(
        "/api/straight-through/calculate",
        json={
            "gas_compositions": [
                {"name": "gas_0", "components": {"nitrogen": 1.0}},
            ],
            "guarantee_gas": "gas_0",
            "data_sheet": {
                "flow": {"magnitude": 100, "unit": "m³/h"},
                "suction_pressure": {"magnitude": 1, "unit": "bar"},
                "suction_temperature": {"magnitude": 300, "unit": "degK"},
                "discharge_pressure": {"magnitude": 5, "unit": "bar"},
                "discharge_temperature": {"magnitude": 400, "unit": "degK"},
                "speed": {"magnitude": 10000, "unit": "rpm"},
                "b": {"magnitude": 28.5, "unit": "mm"},
                "D": {"magnitude": 365, "unit": "mm"},
            },
            "options": {},
        },
    )
    assert response.status_code == 422


def test_straight_through_missing_options(client):
    """Test that missing options returns 422."""
    response = client.post(
        "/api/straight-through/calculate",
        json={
            "gas_compositions": [
                {"name": "gas_0", "components": {"nitrogen": 1.0}},
            ],
            "guarantee_gas": "gas_0",
            "data_sheet": {
                "flow": {"magnitude": 100, "unit": "m³/h"},
                "suction_pressure": {"magnitude": 1, "unit": "bar"},
                "suction_temperature": {"magnitude": 300, "unit": "degK"},
                "discharge_pressure": {"magnitude": 5, "unit": "bar"},
                "discharge_temperature": {"magnitude": 400, "unit": "degK"},
                "speed": {"magnitude": 10000, "unit": "rpm"},
                "b": {"magnitude": 28.5, "unit": "mm"},
                "D": {"magnitude": 365, "unit": "mm"},
            },
            "test_points": [
                {
                    "flow": {"magnitude": 100, "unit": "m³/h"},
                    "suction_pressure": {"magnitude": 1, "unit": "bar"},
                    "suction_temperature": {"magnitude": 300, "unit": "degK"},
                    "discharge_pressure": {"magnitude": 5, "unit": "bar"},
                    "discharge_temperature": {"magnitude": 400, "unit": "degK"},
                    "speed": {"magnitude": 10000, "unit": "rpm"},
                    "gas_name": "gas_0",
                },
            ],
        },
    )
    assert response.status_code == 422


def test_straight_through_invalid_data_sheet(client):
    """Test that a data_sheet with missing required fields returns 422."""
    response = client.post(
        "/api/straight-through/calculate",
        json={
            "gas_compositions": [
                {"name": "gas_0", "components": {"nitrogen": 1.0}},
            ],
            "guarantee_gas": "gas_0",
            "data_sheet": {
                "flow": {"magnitude": 100, "unit": "m³/h"},
                # missing suction_pressure, etc.
            },
            "test_points": [],
            "options": {},
        },
    )
    assert response.status_code == 422
