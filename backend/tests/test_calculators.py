def test_bmi_calculation(client):
    response = client.post(
        "/api/v1/calculators/bmi",
        json={"weight_kg": 70, "height_cm": 175},
        headers={"x-dev-user-id": "test-user"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["bmi"] > 0
    assert body["category"] in {"underweight", "healthy", "overweight", "obese"}


def test_calorie_calculation(client):
    response = client.post(
        "/api/v1/calculators/calories",
        json={
            "gender": "Male",
            "weight_kg": 70,
            "height_cm": 175,
            "age": 30,
            "activity_multiplier": 1.55,
        },
        headers={"x-dev-user-id": "test-user"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["maintenance_calories"] > body["bmr"]
