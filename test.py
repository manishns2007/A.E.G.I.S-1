import os
import requests

file = os.path.join('samples', 'authentic_portrait.jpg')
if not os.path.exists(file):
    import sample_generator
    sample_generator.generate_all_samples()
res = requests.post('http://localhost:8000/api/upload', files={'file': open(file, 'rb')})
cid = res.json()['case_id']
print('Case ID:', cid)
res2 = requests.post('http://localhost:8000/api/analyze', json={'case_id': cid, 'gemini_api_key': ''})
print('Analyze status:', res2.status_code)
print('Response:', res2.text)
