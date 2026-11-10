import sys, json, urllib.request, xml.etree.ElementTree as ET
sys.path.insert(0, r"D:\aitraining")
body={"melody":[
 {"pitch":64,"duration":"half","is_downbeat":True},{"pitch":65,"duration":"half","is_downbeat":False},
 {"pitch":67,"duration":"half","is_downbeat":True},{"pitch":64,"duration":"half","is_downbeat":False},
 {"pitch":62,"duration":"half","is_downbeat":True},{"pitch":60,"duration":"whole","is_downbeat":False}],
 "key":{"tonic":"C","mode":"Major"},"time_signature":"4/4","allow_extended_ranges":False,"allow_secondary_dominants":True,"max_plans":50}
req=urllib.request.Request("http://127.0.0.1:8000/api/harmonize", data=json.dumps(body).encode(), headers={"Content-Type":"application/json"})
d=json.loads(urllib.request.urlopen(req).read())
xml=d["candidates"][0]["musicxml"]
root=ET.fromstring(xml)
for m in root.findall(".//measure"):
    notes=m.findall("note")
    total=sum(int(n.find("duration").text) for n in notes if n.find("voice").text=="1")
    backs=[int(b.find("duration").text) for b in m.findall("backup")]
    print("measure",m.get("number"),"voice1 total divisions",total,"(16=4/4 bar)","backups",backs,"notes",len(notes))
print("durations",d["candidates"][0]["durations"])
