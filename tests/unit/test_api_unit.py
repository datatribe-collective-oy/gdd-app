from fastapi.testclient import TestClient
from scripts.api import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == "Hello World"

def test_get_gdd():
    response = client.get("/api/gdd/")
    assert response.status_code == 200
    assert response.json() == {"message": "Get GDD"}

def test_get_weather():
    response = client.get("/api/weather/")
    assert response.status_code == 200
    assert response.json() == {"message": "Estimate Weather"}