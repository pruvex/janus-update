import json

with open('data/backlog.snapshot.json', encoding='utf-8') as f:
    data = json.load(f)

ready_items = [i for i in data['items'] if i['section'] == 'READY']
print('READY Items:')
for i in ready_items:
    print(f"{i['id']}: {i['type']} - {i['title']}")
