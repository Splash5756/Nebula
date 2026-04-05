import nebula.ast_nodes as ast

class CodeGen:
    def __init__(self, compiler_context: dict):
        self.compiler_context = compiler_context
        self.h_blocks = []
        self.c_blocks = []
        self.current_class = None

        # Headers initial setup
        self.h_blocks.append("#ifndef NEBULA_OUT_H")
        self.h_blocks.append("#define NEBULA_OUT_H\n")
        self.h_blocks.append('#include "nebula_runtime.h"\n')
        self.c_blocks.append('#include "output.h"\n')

    def generate(self, ast_root: ast.ProgramNode):
        # Yabancı dil yönlendirme tabanı (Router Dummy Logic)
        if "python" in self.compiler_context.get("target_langs", []):
            self.c_blocks.append("// GÜVENLİK DUVARI: ROUTER -> Python kodu algılandı. Python API event_loop_mock.h import edilecek.")
            self.c_blocks.append('#include "libs/python_bridge_mock.h"\n')

        for node in ast_root.body:
            self._visit(node)
            
        self.h_blocks.append("\n#endif // NEBULA_OUT_H")
        
        return "\n".join(self.h_blocks), "\n".join(self.c_blocks)

    def _visit(self, node: ast.AstNode):
        if isinstance(node, ast.ClassDeclNode):
            self.current_class = node.name
            
            # 1. C Struct Oluştur (Zero-overhead V-Table mapping için taban)
            struct_str = f"typedef struct {{\n    // Nebula Class: {node.name}\n}} {node.name};\n"
            self.h_blocks.append(struct_str)
            
            for member in node.body:
                self._visit(member)
                
            self.current_class = None

        elif isinstance(node, ast.FuncDeclNode):
            if node.is_async:
                self._generate_async_func(node)
            else:
                self._generate_sync_func(node)

        elif isinstance(node, ast.VarDeclNode):
            if not self.current_class:
                # Global Variable
                c_type_map = {"int": "int", "string": "char*", "float": "float"}
                c_type = c_type_map.get(node.var_type, "void*")
                
                init_str = ""
                if node.init_value:
                    if isinstance(node.init_value, ast.NumberLiteralNode):
                        init_str = f" = {node.init_value.value}"
                    elif isinstance(node.init_value, ast.StringLiteralNode):
                        init_str = f' = "{node.init_value.value}"'
                
                self.h_blocks.append(f"extern {c_type} {node.name};")
                self.c_blocks.append(f"{c_type} {node.name}{init_str};  // line {node.line}")

        # Meta tags ve include node'ları saf C çıktısında yansıtılmaz (preprocessor düzeyinde veya runtime config düzeyindedir)

    def _generate_sync_func(self, node: ast.FuncDeclNode):
        # Global veya Sınıf fonksiyonu mu?
        prefix = ""
        param_str = ""
        
        if self.current_class:
            prefix = f"{self.current_class}_"
            param_str = f"{self.current_class}* this"
            
        func_name = f"{prefix}{node.name}"
        
        sig = f"void {func_name}({param_str})"
        self.h_blocks.append(f"{sig};")
        
        self.c_blocks.append(f"#line {node.line} \"{node.file_path}\"")
        self.c_blocks.append(f"{sig} {{")
        
        # Basit body üretimi (VarDecl vs.)
        for body_node in node.body:
            if isinstance(body_node, ast.VarDeclNode):
                c_type_map = {"int": "int", "string": "char*", "float": "float"}
                c_type = c_type_map.get(body_node.var_type, "void*")
                
                init_str = ""
                if body_node.init_value and isinstance(body_node.init_value, ast.NumberLiteralNode):
                    init_str = f" = {body_node.init_value.value}"
                    
                self.c_blocks.append(f"    {c_type} {body_node.name}{init_str};")
                
        self.c_blocks.append("}\n")

    def _generate_async_func(self, node: ast.FuncDeclNode):
        # State Machine Context Struct Üretimi
        prefix = ""
        if self.current_class:
            prefix = f"{self.current_class}_"
            
        func_name = f"{prefix}{node.name}"
        context_name = f"{func_name}_Context"
        
        # Context struct tanımlaması
        ctx_decl = f"typedef struct {{\n    int state;\n"
        if self.current_class:
            ctx_decl += f"    {self.current_class}* this;\n"
            
        # Lokal değişkenleri state context içine taşı
        local_vars = []
        for body_node in node.body:
            if isinstance(body_node, ast.VarDeclNode):
                c_type_map = {"int": "int", "string": "char*", "float": "float"}
                c_type = c_type_map.get(body_node.var_type, "void*")
                ctx_decl += f"    {c_type} {body_node.name};\n"
                local_vars.append(body_node)
                
        ctx_decl += f"}} {context_name};\n"
        self.h_blocks.append(ctx_decl)
        
        # Fonksiyon imzası
        sig = f"int {func_name}({context_name}* ctx)"
        self.h_blocks.append(f"{sig};")
        
        # Fonksiyon Gövdesi (State Machine)
        self.c_blocks.append(f"#line {node.line} \"{node.file_path}\"")
        self.c_blocks.append(f"{sig} {{")
        self.c_blocks.append("    switch(ctx->state) {")
        self.c_blocks.append("        case 0:")
        
        current_state = 0
        
        for body_node in node.body:
            if isinstance(body_node, ast.VarDeclNode):
                if body_node.init_value and isinstance(body_node.init_value, ast.NumberLiteralNode):
                    self.c_blocks.append(f"            ctx->{body_node.name} = {body_node.init_value.value};")
            
            elif isinstance(body_node, ast.AwaitCallNode):
                # Await noktası: Nebula runtime'a yield et.
                next_state = current_state + 1
                self.c_blocks.append(f"            // await çağrısı: Nebula Green Thread Yield noktası")
                self.c_blocks.append(f"            ctx->state = {next_state};")
                # Farazi async_submit çağrısı
                if isinstance(body_node.func_call, ast.FuncCallNode):
                    self.c_blocks.append(f"            nebula_submit_await({body_node.func_call.name});")
                self.c_blocks.append(f"            return 1; // Pending flag don")
                self.c_blocks.append(f"        case {next_state}:")
                current_state = next_state
                
        self.c_blocks.append("            ctx->state = -1; // Tamamlandı")
        self.c_blocks.append("            return 0; // Bitti")
        self.c_blocks.append("    }")
        self.c_blocks.append("    return 0;")
        self.c_blocks.append("}\n")
