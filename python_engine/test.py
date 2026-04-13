import os
import json

_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_dir, 'test.json'), encoding='utf-8') as f:
    state = json.load(f)

print(type(state))
print(state['map'].keys())