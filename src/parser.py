from typing import List, Optional, Any
from nebula.lexer import Token, TokenType
import nebula.ast_nodes as ast

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        
        # Yığın Tabanlı Kapsam İzolasyonu (LIFO Stack)
        # Her scope içerisinde o dosyaya özel tanımlanan meta-kurallar, operatörler veya typelar barınır.
        self.scope_stack: List[dict] = [{
            "scope_name": "global",
            "meta_rules": []
        }]

    def peek(self) -> Optional[Token]:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def advance(self) -> Optional[Token]:
        token = self.peek()
        self.pos += 1
        return token

    def match(self, expected_type: str, expected_value: Optional[str] = None) -> bool:
        token = self.peek()
        if not token:
            return False
        if token.type == expected_type and (expected_value is None or token.value == expected_value):
            return True
        return False

    def expect(self, expected_type: str, expected_value: Optional[str] = None) -> Token:
        token = self.advance()
        if not token or token.type != expected_type or (expected_value is not None and token.value != expected_value):
            raise SyntaxError(f"Expected {expected_type} '{expected_value}', got {token.type} '{token.value if token else 'EOF'}' at line {token.line if token else 'EOF'}")
        return token

    def parse(self) -> ast.ProgramNode:
        prog_node = ast.ProgramNode()
        while self.peek() and self.peek().type != TokenType.EOF:
            stmt = self.parse_statement()
            if stmt:
                prog_node.body.append(stmt)
        return prog_node

    def parse_statement(self) -> Optional[ast.AstNode]:
        token = self.peek()
        
        if token.type == TokenType.INCLUDE_BEGIN:
            self.advance()
            filename = token.value
            # Yeni kapsama giriyoruz (Push)
            self.scope_stack.append({
                "scope_name": filename,
                "meta_rules": []
            })
            return ast.IncludeBeginNode(filename, line=token.line)
            
        if token.type == TokenType.INCLUDE_END:
            self.advance()
            # Kapsamdan çıkıyoruz, buradaki özel kurallar ölüyor (Pop)
            popped_scope = self.scope_stack.pop()
            return ast.IncludeEndNode(line=token.line)
            
        if token.type == TokenType.COMPILER_BEGIN:
            self.advance() # COMPILER_BEGIN'i atla
            xml_token = self.expect(TokenType.XML_BLOCK)
            self.expect(TokenType.COMPILER_END)
            
            # Dinamik Kuralı bulunduğu yığına ekliyoruz
            self.scope_stack[-1]["meta_rules"].append(xml_token.value)
            return ast.CompilerBlockNode(xml_token.value, line=token.line)

        if token.type == TokenType.KEYWORD:
            if token.value == "class":
                return self.parse_class_decl()
            if token.value == "func":
                return self.parse_func_decl(is_async=False)
            if token.value == "async":
                self.advance() # Asynci atla
                self.expect(TokenType.KEYWORD, "func")
                return self.parse_func_decl(is_async=True)
            if token.value == "let":
                return self.parse_var_decl()

        # Expr statements (örn: await call)
        expr = self.parse_expression()
        self.expect(TokenType.PUNCTUATION, ";")
        return expr

    def parse_class_decl(self) -> ast.ClassDeclNode:
        token = self.expect(TokenType.KEYWORD, "class")
        name_tok = self.expect(TokenType.IDENTIFIER)
        self.expect(TokenType.PUNCTUATION, "{")
        
        body = []
        while self.peek() and not self.match(TokenType.PUNCTUATION, "}"):
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)
        
        self.expect(TokenType.PUNCTUATION, "}")
        return ast.ClassDeclNode(name=name_tok.value, body=body, line=token.line)

    def parse_func_decl(self, is_async: bool) -> ast.FuncDeclNode:
        name_tok = self.expect(TokenType.IDENTIFIER)
        self.expect(TokenType.PUNCTUATION, "(")
        
        # Basit param parsing (name: type) - şimdilik geçiyoruz
        params = []
        while not self.match(TokenType.PUNCTUATION, ")"):
            self.advance()
        self.expect(TokenType.PUNCTUATION, ")")
        
        ret_type = "void"
        # body
        self.expect(TokenType.PUNCTUATION, "{")
        body = []
        while self.peek() and not self.match(TokenType.PUNCTUATION, "}"):
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)
        
        self.expect(TokenType.PUNCTUATION, "}")
        
        return ast.FuncDeclNode(
            name=name_tok.value, 
            params=params, 
            ret_type=ret_type, 
            body=body, 
            is_async=is_async, 
            line=name_tok.line
        )

    def parse_var_decl(self) -> ast.VarDeclNode:
        start_tok = self.expect(TokenType.KEYWORD, "let")
        name_tok = self.expect(TokenType.IDENTIFIER)
        
        # Type
        self.expect(TokenType.PUNCTUATION, ":")
        type_tok = self.expect(TokenType.IDENTIFIER)
        
        # Init
        self.expect(TokenType.operator, "=")
        init_expr = self.parse_expression()
        self.expect(TokenType.PUNCTUATION, ";")
        
        return ast.VarDeclNode(name=name_tok.value, var_type=type_tok.value, init_value=init_expr, line=start_tok.line)

    def parse_expression(self) -> ast.AstNode:
        token = self.peek()
        
        if token.type == TokenType.KEYWORD:
            if token.value == "await":
                await_tok = self.advance()
                call_expr = self.parse_expression()
                return ast.AwaitCallNode(func_call=call_expr, line=await_tok.line)
            if token.value == "ignore":
                ignore_tok = self.advance()
                call_expr = self.parse_expression()
                return ast.IgnoreCallNode(func_call=call_expr, line=ignore_tok.line)

        if token.type == TokenType.IDENTIFIER:
            ident_tok = self.advance()
            # Fonksiyon çağrısı mı?
            if self.match(TokenType.PUNCTUATION, "("):
                self.advance()
                args = []
                while not self.match(TokenType.PUNCTUATION, ")"):
                    args.append(self.parse_expression())
                    if self.match(TokenType.PUNCTUATION, ","):
                        self.advance()
                self.expect(TokenType.PUNCTUATION, ")")
                return ast.FuncCallNode(name=ident_tok.value, args=args, line=ident_tok.line)
            return ast.IdentifierNode(name=ident_tok.value, line=ident_tok.line)
            
        if token.type == TokenType.NUMBER:
            tok = self.advance()
            return ast.NumberLiteralNode(value=tok.value, line=tok.line)
            
        if token.type == TokenType.STRING:
            tok = self.advance()
            return ast.StringLiteralNode(value=tok.value, line=tok.line)

        self.advance()
        return ast.ExprNode(line=token.line)
