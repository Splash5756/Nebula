import nebula.ast_nodes as ast

class SemanticError(Exception):
    pass

class SemanticAnalyzer:
    def __init__(self):
        self.global_vars = set()

    def analyze(self, ast_root: ast.ProgramNode):
        # Nebula OOP felsefesi: Program seviyesinde sadece Class, Include ve CompilerBlock bulunabilir.
        for node in ast_root.body:
            if isinstance(node, ast.IncludeBeginNode) or isinstance(node, ast.IncludeEndNode) or isinstance(node, ast.CompilerBlockNode):
                continue
            if not isinstance(node, ast.ClassDeclNode):
                raise SemanticError(f"Fatal Error: Nebula saf nesne yönelimli bir dildir. Tüm tanımlamalar bir 'class' içerisinde yapılmalıdır! C# standartları ihlali. Hatalı Node: {node.__class__.__name__} at line {node.line}")

        # 2. Fonksiyonları analiz et (Sadece class içindekiler)
        for node in ast_root.body:
            if isinstance(node, ast.ClassDeclNode):
                for member in node.body:
                    if isinstance(member, ast.FuncDeclNode):
                        self._analyze_function(member)

    def _analyze_function(self, func_node: ast.FuncDeclNode):
        if not func_node.is_async:
            return

        # Asenkron fonksiyon analizleri
        self._check_async_body(func_node, func_node.body)

    def _check_async_body(self, func_node: ast.FuncDeclNode, body: list):
        for stmt in body:
            if isinstance(stmt, ast.VarDeclNode):
                if stmt.init_value:
                    self._check_async_expr(func_node, stmt.init_value)
            elif isinstance(stmt, ast.FuncCallNode):
                self._check_async_expr(func_node, stmt)
            elif isinstance(stmt, ast.IdentifierNode):
                self._check_async_expr(func_node, stmt)
            elif isinstance(stmt, ast.AwaitCallNode) or isinstance(stmt, ast.IgnoreCallNode):
                self._check_async_expr(func_node, stmt.func_call)
                
            # Alt gövdesi olan yapılar (if/else/while vb. olsaydı eklenecekti, şimdilik basit geçildi)

    def _check_async_expr(self, func_node: ast.FuncDeclNode, expr: ast.AstNode):
        if isinstance(expr, ast.FuncCallNode):
            # Recursion Koruması
            if expr.name == func_node.name:
                raise SemanticError(f"Fatal Error: Asenkron fonksiyon '{func_node.name}' kendini çağıramaz (Recursion Yasağı) - Satır: {expr.line}")
            for arg in expr.args:
                self._check_async_expr(func_node, arg)

        elif isinstance(expr, ast.IdentifierNode):
            # Global Değişken Koruması
            if expr.name in self.global_vars:
                raise SemanticError(f"Fatal Error: Asenkron fonksiyon '{func_node.name}', '{expr.name}' global değişkenine erişemez (Race Condition Koruması) - Satır: {expr.line}")
