def test_blotter_missing_param(client):
    """Test 400 error when date param is missing."""
    response = client.get("/blotter")
    assert response.status_code == 400
    assert "Missing required parameter" in response.json["error"]


def test_blotter_invalid_date(client):
    """Test 400 error when date format is wrong."""
    response = client.get("/blotter?date=01-15-2025")
    assert response.status_code == 400
    assert "Invalid date format" in response.json["error"]


def test_blotter_success(client, seed_data):
    """Test retrieving trades for a specific date."""
    response = client.get("/blotter?date=2025-01-15")

    assert response.status_code == 200
    data = response.json
    assert len(data) == 2

    first_trade = data[0]
    assert "ticker" in first_trade
    assert "total_value" in first_trade
    assert first_trade["account"] in ["ACC001", "ACC002"]


def test_blotter_empty_date(client, seed_data):
    """Test a date that has no trades."""
    response = client.get("/blotter?date=1999-01-01")
    assert response.status_code == 200
    assert response.json == []
