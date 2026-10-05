import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('DATA_GO_KR_API_KEY')

print("--- 1. 경기도 위험물제조소등 현황 ---")
gg_url = "https://openapi.gg.go.kr/DangerousArticleManufactory"
resp = requests.get(gg_url, params={'Type': 'json', 'pIndex': 1, 'pSize': 3})
print("GG Status:", resp.status_code)
print("GG Response:", resp.text[:300])

print("\n--- 2. KOSHA MSDS API ---")
# Check operations for KOSHA
kosha_url = "https://apis.data.go.kr/B552468/msdschem1/getMsdschemList01"
resp = requests.get(kosha_url, params={'serviceKey': api_key, 'pageNo': 1, 'numOfRows': 3, 'resultType': 'json'})
print("KOSHA Status:", resp.status_code)
print("KOSHA Response:", resp.text[:300])
