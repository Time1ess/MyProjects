class TrieNode(object):
    def __init__(self):
        self.children = {}
        self.end = False

    def get_all_leaf_paths(self, prefix):
        res = set()
        if self.end:
            res.add(prefix)
        for ch, node in self.children.items():
            res = res | node.get_all_leaf_paths(prefix + ch)
        return res


class AutoCompleter(object):
    def __init__(self):
        self.trie_root = TrieNode()

    def add_query(self, query):
        node = self.trie_root
        for ch in query:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.end = True

    def auto_complete(self, query):
        node = self.trie_root
        for ch in query:
            if ch not in node.children:
                return set()
            node = node.children[ch]
        return node.get_all_leaf_paths(query)
