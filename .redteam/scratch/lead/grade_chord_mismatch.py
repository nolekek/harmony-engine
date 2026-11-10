import json, urllib.request
def post(url,p):
    req=urllib.request.Request(url,data=json.dumps(p).encode(),headers={"Content-Type":"application/json"}); return json.loads(urllib.request.urlopen(req).read())
v=[{"soprano":64,"alto":60,"tenor":55,"bass":48}]  # C major chord
for ch in (["V"],["D"],["T"],["I"]):
    r=post("http://127.0.0.1:8000/api/grade",{"voicings":v,"key":{"tonic":"C","mode":"Major"},"chords":ch,"time_signature":"4/4"})["report"]
    print(ch,"->",r["grade"],"hard",r["hard_violations_count"],[(x["rule_id"],x["message_ru"]) for x in r["violations"]])
