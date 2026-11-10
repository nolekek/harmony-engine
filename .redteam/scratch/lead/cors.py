import http.client
c=http.client.HTTPConnection("127.0.0.1",8000,timeout=5)
c.request("GET","/api/health",headers={"Origin":"http://evil.com"})
r=c.getresponse(); print(r.status); 
for k,v in r.getheaders():
    if k.lower().startswith("access-control"): print(k+":",v)
