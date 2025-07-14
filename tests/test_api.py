import os, sys, pytest
# Add the parent directory (project root) to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c

def test_calendar(client):
    """GET /api/calendar/2025 should return a list of races."""
    res = client.get('/api/calendar/2025')
    assert res.status_code == 200
    data = res.get_json()
    assert 'races' in data
    assert isinstance(data['races'], list)
    # each race has round & raceName
    for race in data['races']:
        assert 'round' in race
        assert 'raceName' in race

def test_season_results(client):
    """GET /api/season/2025/results/1?session=R returns results."""
    res = client.get('/api/season/2025/results/1?session=R')
    assert res.status_code == 200
    data = res.get_json()
    assert 'results' in data
    assert isinstance(data['results'], list)
    # check presence of key fields in first result
    if data['results']:
        first = data['results'][0]
        for key in ('position','driver','time','gap','status','constructor'):
            assert key in first

def test_latest(client):
    """GET /api/latest returns season, round, session & results."""
    res = client.get('/api/latest')
    assert res.status_code == 200
    data = res.get_json()
    for key in ('season','round','session','results'):
        assert key in data
    assert isinstance(data['results'], list)
