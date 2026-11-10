import json, urllib.request
def post(url, payload):
    req=urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(req).read())
for name, p in [("C major scale",[60,62,64,65,67,69,71,72]), ("A harmonic minor",[69,71,72,74,76,77,80,81]), ("default E F G E D C",[64,65,67,64,62,60]), ("A natural minor",[69,71,72,74,76,77,79,81])]:
    r=post("http://127.0.0.1:8000/api/detect-key", [{"pitch":x} for x in p])
    print(name, "->", r.get("name"), r.get("tonic"), r.get("mode"), "fifths", r.get("fifths"))
