import requests

# 1. Info API Test
r_info = requests.get('http://127.0.0.1:8000/api/hazmat/info?name=신나')
print('Info API Status:', r_info.status_code)
data_info = r_info.json()
print('분류:', data_info.get('hazard_class'), data_info.get('class_name'), '>', data_info.get('item_name'))
print('위험등급:', data_info.get('danger_rank'))
print('인화점:', data_info.get('flash_point'))
print('주의표지:', data_info.get('caution_sign'))
print('지정수량:', data_info.get('designated_qty'), data_info.get('unit'), '/ 조례(0.2배):', data_info.get('gg_small_qty_threshold'))
print('저장수칙 1:', data_info.get('storage_rules', [''])[0])
print('소화방법:', data_info.get('extinguish_method'))

# 2. Catalog API Test
r_cat = requests.get('http://127.0.0.1:8000/api/hazmat/catalog?q=아세톤')
print('\nCatalog API Status:', r_cat.status_code)
data_cat = r_cat.json()
print('검색된 물질 수:', len(data_cat))
if data_cat:
    print('첫번째 항목:', data_cat[0]['item_name'], '(수용성:', data_cat[0].get('is_water_soluble'), ')')
