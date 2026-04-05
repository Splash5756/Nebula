from typing import List, Optional, Any

class AstNode:
    def __init__(self, line: int = 0, file_path: str = ""):
        self.line = line
        self.file_path = file_path

class ProgramNode(AstNode):
    """Kök düğüm."""
    def __init__(self, line=0, file_path=""):
        super().__init__(line, file_path)
        self.body: List['AstNode'] = []

class IncludeBeginNode(AstNode):
    """#include-begin bayrağını temsil eder Kapsam Push başlar."""
    def __init__(self, target_file: str, line=0, file_path=""):
        super().__init__(line, file_path)
        self.target_file = target_file

class IncludeEndNode(AstNode):
    """#include-end bayrağı Kapsam Pop gerçekleşir."""
    pass

class CompilerBlockNode(AstNode):
    """#compiler-begin ile #compiler-end arasındaki XML/HTML benzeri tagları barındırır."""
    def __init__(self, raw_xml: str, line=0, file_path=""):
        super().__init__(line, file_path)
        self.raw_xml = raw_xml

class ClassDeclNode(AstNode):
    """Sınıf deklarasyonu (C tarafında struct'a dönüşecek)"""
    def __init__(self, name: str, body: List['AstNode'], line=0, file_path=""):
        super().__init__(line, file_path)
        self.name = name
        self.body = body

class FuncDeclNode(AstNode):
    """Fonksiyon deklarasyonu. is_async true ise green thread state machine'e dönüşecektir."""
    def __init__(self, name: str, params: List[dict], ret_type: str, body: List['AstNode'], is_async: bool = False, line=0, file_path=""):
        super().__init__(line, file_path)
        self.name = name
        self.params = params  # Örn: [{"name": "x", "type": "int"}]
        self.ret_type = ret_type
        self.body = body
        self.is_async = is_async

class VarDeclNode(AstNode):
    """Değişken Deklarasyonu"""
    def __init__(self, name: str, var_type: str, init_value: Optional['AstNode'] = None, line=0, file_path=""):
        super().__init__(line, file_path)
        self.name = name
        self.var_type = var_type
        self.init_value = init_value

class AwaitCallNode(AstNode):
    """await func() - Green Thread yield/resume noktası"""
    def __init__(self, func_call: 'AstNode', line=0, file_path=""):
        super().__init__(line, file_path)
        self.func_call = func_call

class IgnoreCallNode(AstNode):
    """ignore func() - Fire and forget asenkron çağrı"""
    def __init__(self, func_call: 'AstNode', line=0, file_path=""):
        super().__init__(line, file_path)
        self.func_call = func_call

class ExprNode(AstNode):
    """İfadeler için taban sınıf"""
    pass

class IdentifierNode(ExprNode):
    def __init__(self, name: str, line=0, file_path=""):
        super().__init__(line, file_path)
        self.name = name

class FuncCallNode(ExprNode):
    def __init__(self, name: str, args: List['AstNode'], line=0, file_path=""):
        super().__init__(line, file_path)
        self.name = name
        self.args = args

class NumberLiteralNode(ExprNode):
    def __init__(self, value: str, line=0, file_path=""):
        super().__init__(line, file_path)
        self.value = value

class StringLiteralNode(ExprNode):
    def __init__(self, value: str, line=0, file_path=""):
        super().__init__(line, file_path)
        self.value = value
