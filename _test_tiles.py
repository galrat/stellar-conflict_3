import re, json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

content = open('tiles.js', encoding='utf-8').read()
content = re.sub(r'//[^\n]*', '', content)

start = content.find('let TILE_CATALOG = [')
if start == -1:
    start = content.find('const TILE_CATALOG = [')
bracket_start = content.index('[', start)

depth, end = 0, bracket_start
for i in range(bracket_start, len(content)):
    if content[i] == '[': depth += 1
    elif content[i] == ']':
        depth -= 1
        if depth == 0: end = i; break

json_str = content[bracket_start:end + 1]
json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
json_str = re.sub(r'([{,\[]\s*\n?\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_str)
json_str = re.sub(r"'([^'\\]*)'", r'"\1"', json_str)

try:
    tiles = json.loads(json_str)
    print('OK, tiles:', len(tiles))
except json.JSONDecodeError as e:
    print('Error:', e)
    print('Context:', repr(json_str[max(0, e.pos-40):e.pos+40]))
