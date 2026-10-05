import requests

payload = {
    'items': [
        {
            'chemical_name': '신나',
            'container_capacity': 55.0,
            'container_unit': 'gal',
            'container_count': 2
        },
        {
            'chemical_name': '경유',
            'container_capacity': 200.0,
            'container_unit': 'L',
            'container_count': 3
        }
    ],
    'location_type': 'unauthorized_place'
}

r = requests.post('http://127.0.0.1:8000/api/calculate', json=payload)
print('Status:', r.status_code)
data = r.json()
print('Total multiple:', data['total_multiple'])
for it in data['item_results']:
    print(f"- {it['name']}: {it['container_desc']} => 총 {it['quantity']}{it['unit']} (배수: {it['multiple']}배)")

doc_payload = {
    'doc_type': 'violation',
    'target': {
        'business_name': '대한케미칼',
        'representative_name': '이몽룡',
        'address': '경기도 화성시 마도면',
        'contact': '031-999-8888',
        'inspector_name': '이국신',
        'inspector_org': '화성소방서'
    },
    'assessment': data
}
r_doc = requests.post('http://127.0.0.1:8000/api/documents/generate', json=doc_payload)
print('\n[서류 내역 미리보기]:')
print(r_doc.json()['document_text'][:500])
