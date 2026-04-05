import re
from typing import List, Optional

class Token:
    def __init__(self, type_: str, value: str, line: int):
        self.type = type_
        self.value = value
        self.line = line

    def __repr__(self):
        return f"Token({self.type}, '{self.value}')"

class Lexer:
    """
    Kör (Agnostic) Lexer.
    Hiçbir statik syntax barındırmaz. Tamamen `MetaScanner`'dan gelen
    RegEx'lere göre çalışarak eşleştirme yapar.
    """
    def __init__(self, code: str, token_rules: List[dict]):
        self.code = code
        self.pos = 0
        self.line = 1
        self.tokens: List[Token] = []
        
        # MetaScanner tarafından core.neb içinden çekilen XML tabanlı token kuralları
        # Örn: [{"name": "KEYWORD_CLASS", "regex": "class"}]
        self.rules = token_rules

    def _advance_whitespace(self):
        while self.pos < len(self.code) and self.code[self.pos].isspace():
            if self.code[self.pos] == '\n':
                self.line += 1
            self.pos += 1

    def tokenize(self) -> List[Token]:
        line_stack = []
        
        while self.pos < len(self.code):
            self._advance_whitespace()
            if self.pos >= len(self.code):
                break
                
            # Preprocessor Sınır Bayrakları için Statik Kontrol
            if self.code[self.pos:].startswith("#include-begin"):
                match = re.match(r'^#include-begin\s+"([^"]+)"', self.code[self.pos:])
                if match:
                    filename = match.group(1)
                    line_stack.append(self.line)  # Parent dosyanın satırını dondur
                    self.line = 1                 # İç dosya için sayacı sıfırla
                    self.tokens.append(Token("INCLUDE_BEGIN", filename, self.line))
                    self.pos += match.end()
                    continue
                    
            if self.code[self.pos:].startswith("#include-end"):
                match = re.match(r'^#include-end', self.code[self.pos:])
                if match:
                    self.tokens.append(Token("INCLUDE_END", "", self.line))
                    if line_stack:
                        self.line = line_stack.pop() # Parent dosyanın satırına geri dön
                    self.pos += match.end()
                    continue

            # Core.neb kurallarından dinamik tarama
            match_found = False
            for rule in self.rules:
                # Sadece başlangıçtan itibaren tam eşleştir
                pattern = f"^{rule['regex']}"
                match = re.match(pattern, self.code[self.pos:])
                if match:
                    val = match.group(0)
                    self.tokens.append(Token(rule['name'], val, self.line))
                    self.pos += len(val)
                    self.line += val.count('\n')
                    match_found = True
                    break
                    
            if not match_found:
                # Bilinmeyen karakter
                char = self.code[self.pos]
                # print(f"Bilinmeyen karakter atlandı: {char} at line {self.line}")
                self.pos += 1

        self.tokens.append(Token("EOF", "", self.line))
        return self.tokens
