import json, urllib.request
def post(url,p):
    req=urllib.request.Request(url,data=json.dumps(p).encode(),headers={"Content-Type":"application/json"}); return json.loads(urllib.request.urlopen(req).read())
voicings=[{"soprano":64,"alto":64,"tenor":60,"bass":48}]
for chords in (["T"], None):
    r=post("http://127.0.0.1:8000/api/grade",{"voicings":voicings,"key":{"tonic":"C","mode":"Major"},"chords":chords,"time_signature":"4/4"})["report"]
    print("chords",chords,"grade",r["grade"],"hard",r["hard_violations_count"],"viol",[(v["rule_id"],v["message_ru"]) for v in r["violations"]])
