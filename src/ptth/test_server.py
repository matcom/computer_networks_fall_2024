import requests

BASE_URL = "http://127.0.0.1:50000"

sess = requests.Session()

#res = requests.get(BASE_URL)
res = sess.post(BASE_URL)
print(res.text)
res = sess.get(BASE_URL)
print(res.text)
