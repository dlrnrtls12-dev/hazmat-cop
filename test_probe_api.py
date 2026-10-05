import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

with open(r'C:\Users\이국신\.gemini\antigravity\brain\358e3a19-3e76-46c6-891b-e8f0f698cc47\.system_generated\steps\50\content.md', encoding='utf-8') as f:
    text = f.read()

pos = text.find('getMaterialList')
params = re.findall(r'data-paramtr-nm="([^"]+)"', text[pos:pos+5000])
print('Found params:', params)

# Test calling the API
api_key = os.getenv('DATA_GO_KR_API_KEY')
url = 'https://apis.data.go.kr/1661000/materialInfoSvc/getMaterialList'
req_params = {
    'serviceKey': api_key,
    'pageNo': 1,
    'numOfRows': 10,
    'resultType': 'json'
}
resp = requests.get(url, params=req_params)
print('Status:', resp.status_code)
print('Response text:', resp.text[:500])
