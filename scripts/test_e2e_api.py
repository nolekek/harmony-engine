import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from backend.main import app

def test_full_pipeline():
    client = TestClient(app)

    # 1. Health
    r = client.get('/api/health')
    assert r.status_code == 200, r.text
    print('Health:', r.json())

    # 2. SPA index
    r = client.get('/')
    assert r.status_code == 200, r.status_code
    assert 'html' in r.text
    print('SPA index served OK, length:', len(r.text))

    # 3. Keys
    r = client.get('/api/keys')
    assert r.status_code == 200
    keys = r.json()
    assert len(keys) == 24
    print('Keys count:', len(keys))

    # 4. Harmonize
    payload = {
        'melody': [
            {'pitch': 64, 'is_downbeat': True, 'duration': 'half'},
            {'pitch': 65, 'is_downbeat': False, 'duration': 'half'},
            {'pitch': 67, 'is_downbeat': True, 'duration': 'half'},
            {'pitch': 64, 'is_downbeat': False, 'duration': 'half'},
            {'pitch': 62, 'is_downbeat': True, 'duration': 'half'},
            {'pitch': 60, 'is_downbeat': False, 'duration': 'whole'}
        ],
        'key': {'tonic': 'C', 'mode': 'Major'},
        'allow_extended_ranges': False,
        'allow_secondary_dominants': True
    }
    r = client.post('/api/harmonize', json=payload)
    assert r.status_code == 200
    harm_data = r.json()
    print('Harmonize success:', harm_data['is_success'], 'Latency:', harm_data['latency_ms'], 'ms', 'Candidates:', len(harm_data['candidates']))
    assert len(harm_data['candidates']) > 0
    cand0 = harm_data['candidates'][0]
    print('Candidate #1:', cand0['description'], 'Cost:', cand0['cost'], 'Chords:', cand0['chords'])

    # 5. Grade
    grade_payload = {
        'voicings': [
            {'soprano': 67, 'alto': 60, 'tenor': 55, 'bass': 48},
            {'soprano': 69, 'alto': 62, 'tenor': 57, 'bass': 50}
        ],
        'key': {'tonic': 'C', 'mode': 'Major'}
    }
    r = client.post('/api/grade', json=grade_payload)
    assert r.status_code == 200
    grade_data = r.json()
    print('Grader report grade:', grade_data['report']['grade'], 'Violations:', len(grade_data['report']['violations']))
    print('Violations breakdown:')
    for v in grade_data['report']['violations']:
        print(' -', v['message_ru'])

    # 6. MIDI and MusicXML export
    r_midi = client.post('/api/export/midi', json={'voicings': cand0['voicings']})
    assert r_midi.status_code == 200
    assert len(r_midi.content) > 50
    print('MIDI export bytes:', len(r_midi.content))

    r_xml = client.post('/api/export/musicxml', json={'voicings': cand0['voicings'], 'key': {'tonic': 'C', 'mode': 'Major'}})
    assert r_xml.status_code == 200
    assert '<score-partwise' in r_xml.text
    print('MusicXML export length:', len(r_xml.text))

    print('\n>>> ALL TEST CHECKS PASSED WITH FLYING COLORS! <<<')

if __name__ == '__main__':
    test_full_pipeline()
