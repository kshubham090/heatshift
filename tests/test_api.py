"""HTTP boundary checks; these inputs are explicit test fixtures."""
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
import backend.app as api
from backend.demo import demo_plan
from backend.models import Weather, WeatherHour
from backend.weather import WeatherUnavailable

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv('HEATSHIFT_RATE_LIMIT','0')
    return TestClient(api.app)

@pytest.fixture
def fixture_weather():
    p=demo_plan()
    return Weather(fetchedAt=datetime.now(timezone.utc).isoformat(),mode='live',date=p.date,
        latitude=p.location.latitude,longitude=p.location.longitude,
        gridLatitude=p.location.latitude,gridLongitude=p.location.longitude,
        hours=[WeatherHour(time=f'{h:02d}:00',temperatureC=20+h/2,apparentTemperatureC=20+h/2,precipitationProbability=0) for h in range(24)],
        attribution='TEST FIXTURE',sourceUrl='https://example.com/test-fixture',warnings=[])

def test_demo_is_wrapped_and_valid(client):
    r=client.get('/api/demo')
    assert r.status_code==200
    assert len(r.json()['plan']['tasks'])==4

def test_valid_plan_uses_adapter_and_preserves_work(client,monkeypatch,fixture_weather):
    calls=[]
    async def weather(lat,lon,date):calls.append((lat,lon,date));return fixture_weather
    monkeypatch.setattr(api,'get_weather',weather)
    p=demo_plan()
    r=client.post('/api/optimize',json=p.model_dump())
    assert r.status_code==200,r.text
    data=r.json()
    assert data['metrics']['workMinutes']==195
    assert len(data['schedule'])==4 and len(calls)==1
    assert data['request']==p.model_dump()

def test_weather_failure_has_no_generated_result(client,monkeypatch):
    async def offline(*args):raise WeatherUnavailable('No date-matched forecast is available.')
    monkeypatch.setattr(api,'get_weather',offline)
    r=client.post('/api/optimize',json=demo_plan().model_dump())
    assert r.status_code==503
    assert 'schedule' not in r.json()
    assert 'date-matched' in r.json()['detail']

def test_invalid_duration_rejected_before_weather(client,monkeypatch):
    p=demo_plan().model_dump();p['tasks'][0]['durationMinutes']=17
    async def forbidden(*args):raise AssertionError('Must not fetch for invalid plan')
    monkeypatch.setattr(api,'get_weather',forbidden)
    assert client.post('/api/optimize',json=p).status_code==422

def test_agent_message_bounded(client):
    assert client.post('/api/agent',json={'message':'x'*2001,'plan':demo_plan().model_dump()}).status_code==422

def test_oversized_request_rejected(client):
    r=client.post('/api/agent',content=b'x'*65537,headers={'Content-Type':'application/json'})
    assert r.status_code==413

def test_unknown_api_does_not_serve_frontend(client):
    assert client.get('/api/not-real').status_code==404

def test_agent_failure_keeps_private_error_out_of_response(client,monkeypatch):
    import backend.agent as agent
    async def unavailable(*args):raise RuntimeError('PRIVATE_PROVIDER_PAYLOAD')
    monkeypatch.setattr(agent,'run_agent',unavailable)
    r=client.post('/api/agent',json={'message':'Please optimise','plan':demo_plan().model_dump()})
    assert r.status_code==503
    assert 'PRIVATE_PROVIDER_PAYLOAD' not in r.text
    assert 'unchanged' in r.json()['detail']

def test_api_headers(client,monkeypatch,fixture_weather):
    async def weather(*args):return fixture_weather
    monkeypatch.setattr(api,'get_weather',weather)
    r=client.post('/api/optimize',json=demo_plan().model_dump())
    assert r.headers['cache-control']=='no-store'
    assert r.headers['x-content-type-options']=='nosniff'
