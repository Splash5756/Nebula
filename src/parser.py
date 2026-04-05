from typing import List, Optional
from src.lexer import Token
from src.generic_node import GenericNode

class Parser:
    """
    Evrensel, XML-tabanlı ayrıştırıcı (Dumb Engine Parser).
    MetaScanner üzerinden gelen `rules` sözlüğünü kullanarak metni GenericNode'lara dönüştürür.
    """
    def __init__(self, tokens: List[Token], rules: List[dict]):
        self.tokens = tokens
        self.pos = 0
        
        # XML'den çıkarılan kuralları dictionary'e çeviriyoruz hızlı erişim için
        # pattern_dict -> "function_declaration": "KEYWORD_FUNC IDENTIFIER LPAREN RPAREN LBRACE BODY RBRACE"
        self.rules_dict = {r["name"]: r["pattern"] for r in rules if "pattern" in r}
        
        self.scope_stack: List[dict] = [{
            "scope_name": "global",
            "meta_rules": []
        }]
        # Dosya ismi izleyici (Path resolution sirasinda gelen INCLUDE_BEGIN tokenlarindan beslenir)
        self.current_file = "unknown.neb"
        self.file_stack = []

    def peek(self) -> Optional[Token]:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def advance(self) -> Optional[Token]:
        token = self.peek()
        self.pos += 1
        return token

    def match(self, expected_type: str) -> bool:
        token = self.peek()
        if not token: return False
        return token.type == expected_type

    def parse(self) -> GenericNode:
        prog_node = GenericNode("Program")
        body = []
        while self.peek() and self.peek().type != "EOF":
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)
            else:
                # Eşleşmeyen bir şey varsa atla (örneğin fazladan noktalı virgül veya boşluk)
                self.advance()
                
        prog_node.set("BODY", body)
        return prog_node

    def parse_statement(self) -> Optional[GenericNode]:
        token = self.peek()
        if not token: return None
        
        if token.type == "INCLUDE_BEGIN":
            self.file_stack.append(self.current_file)
            self.current_file = token.value
            self.advance()
            return GenericNode("IncludeBegin", line=token.line)
            
        if token.type == "INCLUDE_END":
            if self.file_stack:
                self.current_file = self.file_stack.pop()
            self.advance()
            return GenericNode("IncludeEnd", line=token.line)

        # XML İçerisinden dinamik parse edilecek Statement Rules araması
        for rule_name, rule_pattern in self.rules_dict.items():
            saved_pos = self.pos
            node = self._try_parse_rule(rule_name, rule_pattern)
            if node:
                return node
            else:
                # Geri sar, başka kural dene
                self.pos = saved_pos

        return None

    def _try_parse_rule(self, rule_name: str, pattern: str) -> Optional[GenericNode]:
        parts = pattern.split(" ")
        node = GenericNode(rule_name)
        node.file = self.current_file
        node.line = self.peek().line if self.peek() else 0
        
        for part in parts:
            if part == "": continue
                
            # Dinamik Olarak Block Okuyucu (BODY keyword'ü bir dizi statement'ı temsil eder)
            if part == "BODY":
                body_list = []
                # Burada RBRACE gelene kadar parse_statement çağırmalı.
                while self.peek() and self.peek().type != "RBRACE":
                    stmt = self.parse_statement()
                    if stmt:
                        body_list.append(stmt)
                    else:
                        break
                node.set("BODY", body_list)
                continue
                
            # Basit Expr Okuru (Detaylar EXPR meta-kuralı veya pratt parsing ile genişletilebilir)
            if part == "EXPR":
                # Şimdilik prototip amaçlı bir sonraki token'ı ifade olarak alıp geçiyoruz. (Sayı, IDENTIFIER vs)
                # Geliştirilmiş sürümde expression-tree inşa edilebilir
                expr_tok = self.advance()
                node.set("EXPR", expr_tok.value)
                continue

            # Diğer tüm kurallar spesifik bir Token tipini bekliyor
            tok = self.peek()
            if tok and tok.type == part:
                node.append_to(part, tok.value)
                self.advance()
            else:
                return None # Kural çöktü, backtrack
                
        return node
