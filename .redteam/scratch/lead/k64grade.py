import json, urllib.request
def post(url,p):
    req=urllib.request.Request(url,data=json.dumps(p).encode(),headers={"Content-Type":"application/json"}); return json.loads(urllib.request.urlopen(req).read())
mel=[{"pitch":x,"duration":"half","is_downbeat":(i%2==0)} for i,x in enumerate([72,67,64,60])]
r=post("http://127.0.0.1:8000/api/harmonize",{"melody":mel,"key":{"tonic":"C","mode":"Major"},"time_signature":"4/4","max_plans":50})
b=r["candidates"][0]
print("chords",b["chords"],"cost",b["cost"],"voicings",[(v["soprano"],v["alto"],v["tenor"],v["bass"]) for v in b["voicings"]])
g=post("http://127.0.0.1:8000/api/grade",{"voicings":b["voicings"],"key":{"tonic":"C","mode":"Major"},"chords":b["chords"],"time_signature":"4/4","durations":b["durations"]})
print("grade",g["report"]["grade"],"valid",g["report"]["is_valid"],"hard",g["report"]["hard_violations_count"],"violations",[(v["rule_id"],v["message_ru"]) for v in g["report"]["violations"]])
