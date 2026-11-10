import json, urllib.request
def post(p):
    req=urllib.request.Request("http://127.0.0.1:8000/api/harmonize", data=json.dumps(p).encode(), headers={"Content-Type":"application/json"})
    try:
        r=urllib.request.urlopen(req); return r.status, json.loads(r.read())
    except Exception as e:
        return getattr(e,'code',None), str(e)
base={"melody":[{"pitch":64,"duration":"half"},{"pitch":65,"duration":"half"},{"pitch":67,"duration":"whole"}],"time_signature":"4/4"}
for extra in [{"key":{"tonic":"Z#","mode":"AlienMode"}},{"key":{"tonic":"C","mode":"Major"},"max_plans":0},{"key":{"tonic":"C","mode":"Major"},"max_plans":-10}]:
    p=dict(base); p.update(extra)
    s,d=post(p)
    print(extra,"->",s, d.get("is_success") if isinstance(d,dict) else d, len(d.get("candidates",[])) if isinstance(d,dict) else "")
