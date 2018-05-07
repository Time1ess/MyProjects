from string import ascii_lowercase
from random import choices

from ac import AutoCompleter


ac = AutoCompleter()
queries = (''.join(choices(ascii_lowercase[:5], k=8)) for _ in range(1000))
search_queries = (
    ''.join(choices(ascii_lowercase[:5], k=4)) for _ in range(10))
for query in queries:
    ac.add_query(query)
for search_query in search_queries:
    print('Query:', search_query)
    print('AutoCompletion:', ac.auto_complete(search_query))
