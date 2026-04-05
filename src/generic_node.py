from typing import List, Optional, Any

class GenericNode:
    """
    Evrensel, Kördüğüm (Agnostic) AST Düğümü.
    Hiçbir sınıf veya C çevirisi bilmez, sadece kuralları taşır.
    """
    def __init__(self, node_type: str, line: int = 0):
        self.type = node_type  # Örn: "ClassDeclaration", "VarDecl"
        self.line = line
        
        # Sadece basit atama ile veri alan, metin tutan kurallar (Örn token value'su)
        self.value: Optional[str] = None
        
        # Etiketli alt ağaç yapısı. (Örn: {"BODY": [...], "IDENTIFIER": GenericNode})
        # Sözlük (Dictionary Lookup) üzerinden kolay erişim sağlar.
        self.children: dict = {}

    def get(self, key: str) -> Any:
        """Kullanıcının `node.get("BODY")` yaklaşımı ile içgüdüsel gezinmesine imkan tanır."""
        return self.children.get(key, None)

    def set(self, key: str, value: Any):
        """Alt dal (node) veya primitive string ekler."""
        self.children[key] = value

    def append_to(self, key: str, value: Any):
        """Aynı isimden (örn parametreler) birden çok varsa Listeye ekler."""
        if key not in self.children:
            self.children[key] = []
        elif not isinstance(self.children[key], list):
            self.children[key] = [self.children[key]]
            
        if isinstance(self.children[key], list):
            self.children[key].append(value)

    def __repr__(self):
        return f"GenericNode(type='{self.type}', children_keys={list(self.children.keys())})"
