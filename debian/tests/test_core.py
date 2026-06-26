import sys
sys.path.insert(0, '.')
from core.q3n import parse
text = '/// https://x.com /// t:\nhello\\\\\\'
e = parse(text)
assert len(e) == 1 and e[0].uri == 'https://x.com'
print('Tests passed')
