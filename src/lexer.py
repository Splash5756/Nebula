import re
from dataclasses import dataclass
from typing import List, Tuple, Optional

# Lexer sabitleri

# Token Türleri
class TokenType:
    KEYWORD = "KEYWORD"
    IDENTIFIER = "IDENTIFIER"
    NUMBER = "NUMBER"
    STRING = "STRING"
    operator = "OPERATOR"
    PUNCTUATION = "PUNCTUATION"
    
    # Preprocessor özel işaretleri
    INCLUDE_BEGIN = "INCLUDE_BEGIN"
    INCLUDE_END = "INCLUDE_END"
    COMPILER_BEGIN = "COMPILER_BEGIN"
    COMPILER_END = "COMPILER_END"
    XML_BLOCK = "XML_BLOCK"  # <define-token> vb için
    EOF = "EOF"

KEYWORDS = {
    "class", "func", "async", "await", "ignore", "return", "if", "else", "let"
}

class Token:
    def __init__(self, type_: str, value: str, line: int):
        self.type = type_
        self.value = value
        self.line = line

    def __repr__(self):
        return f"Token({self.type}, '{self.value}', line={self.line})"

class Lexer:
    def __init__(self, code: str):
        self.code = code
        self.pos = 0
        self.line = 1
        self.tokens: List[Token] = []
        
        self.in_compiler_block = False
        
    def advance(self):
        if self.pos < len(self.code):
            if self.code[self.pos] == '\n':
                self.line += 1
            self.pos += 1

    def peek(self) -> Optional[str]:
        if self.pos < len(self.code):
            return self.code[self.pos]
        return None

    def tokenize(self) -> List[Token]:
        while self.pos < len(self.code):
            char = self.code[self.pos]

            if char.isspace():
                self.advance()
                continue
            
            # Yorum Satırları veya Compiler Direktifleri
            if char == '#':
                directive_match = self._match_directive()
                if directive_match:
                    continue  # Directive token olarak eklendi içeride
            
            if self.in_compiler_block:
                # #compiler-begin / end arasındaki her şeyi raw XML block olarak okuyalım
                xml_content = self._consume_until("#compiler-end")
                self.tokens.append(Token(TokenType.XML_BLOCK, xml_content.strip(), self.line))
                self.in_compiler_block = False
                continue

            if char.isalpha() or char == '_':
                ident = self._consume_ident()
                if ident in KEYWORDS:
                    self.tokens.append(Token(TokenType.KEYWORD, ident, self.line))
                else:
                    self.tokens.append(Token(TokenType.IDENTIFIER, ident, self.line))
                continue
                
            if char.isdigit():
                num = self._consume_number()
                self.tokens.append(Token(TokenType.NUMBER, num, self.line))
                continue
                
            if char == '"':
                string_val = self._consume_string()
                self.tokens.append(Token(TokenType.STRING, string_val, self.line))
                continue
                
            if char in "{}();:,":
                self.tokens.append(Token(TokenType.PUNCTUATION, char, self.line))
                self.advance()
                continue
                
            if char in "+-*/=<>!":
                op = self._consume_operator()
                self.tokens.append(Token(TokenType.operator, op, self.line))
                continue
                
            # Bilinmeyen karakter
            print(f"Bilinmeyen karakter: {char} at line {self.line}")
            self.advance()

        self.tokens.append(Token(TokenType.EOF, "", self.line))
        return self.tokens

    def _match_directive(self) -> bool:
        start_pos = self.pos
        # #include-begin "file.nep" stringi veya benzerleri
        rest_of_line = self._consume_until("\n")
        
        if rest_of_line.startswith("#include-begin"):
            parts = rest_of_line.split(" ", 1)
            filename = parts[1].strip() if len(parts) > 1 else ""
            self.tokens.append(Token(TokenType.INCLUDE_BEGIN, filename.strip('"'), self.line))
            return True
        elif rest_of_line.startswith("#include-end"):
            self.tokens.append(Token(TokenType.INCLUDE_END, "", self.line))
            return True
        elif rest_of_line.startswith("#compiler-begin"):
            self.tokens.append(Token(TokenType.COMPILER_BEGIN, "", self.line))
            self.in_compiler_block = True
            return True
        elif rest_of_line.startswith("#compiler-end"):
            self.tokens.append(Token(TokenType.COMPILER_END, "", self.line))
            self.in_compiler_block = False
            return True
        
        # Eğer directive değilse normal yoruma dönsün geri
        self.pos = start_pos
        line_comment = self._consume_until("\n")
        return True # Yorum satırı saydık

    def _consume_ident(self) -> str:
        start = self.pos
        while self.peek() and (self.peek().isalnum() or self.peek() == '_'):
            self.advance()
        return self.code[start:self.pos]

    def _consume_number(self) -> str:
        start = self.pos
        while self.peek() and self.peek().isdigit():
            self.advance()
        return self.code[start:self.pos]

    def _consume_string(self) -> str:
        self.advance() # '"'
        start = self.pos
        while self.peek() and self.peek() != '"':
            self.advance()
        val = self.code[start:self.pos]
        self.advance() # '"'
        return val

    def _consume_operator(self) -> str:
        start = self.pos
        while self.peek() and self.peek() in "+-*/=<>!":
            self.advance()
        return self.code[start:self.pos]

    def _consume_until(self, substring: str) -> str:
        start = self.pos
        idx = self.code.find(substring, self.pos)
        if idx == -1:
            val = self.code[self.pos:]
            self.pos = len(self.code)
            return val
        
        val = self.code[self.pos:idx]
        self.pos = idx
        if substring == "\n":
            self.advance() # Consume newline
        return val
