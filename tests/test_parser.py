import json
from nebula.lexer import Lexer
from nebula.parser import Parser

def dump_ast(node, indent=0):
    spacing = "  " * indent
    if node is None:
        print(spacing + "None")
        return
        
    class_name = node.__class__.__name__
    props = []
    
    for key, value in node.__dict__.items():
        if key in ("line", "file_path"):
            continue
            
        if isinstance(value, list) and len(value) > 0 and hasattr(value[0], "__dict__"):
            props.append(f"{key}=List[...]")
        elif hasattr(value, "__dict__"):
            props.append(f"{key}=<Node>")
        else:
            props.append(f"{key}={repr(value)}")
            
    prop_str = ", ".join(props)
    print(f"{spacing}- {class_name}({prop_str})")
    
    # Recursively print body if exists
    if hasattr(node, "body") and isinstance(node.body, list):
        for child in node.body:
            dump_ast(child, indent + 1)
    
    if hasattr(node, "func_call"):
        dump_ast(node.func_call, indent + 1)
        
    if hasattr(node, "init_value") and node.init_value:
        dump_ast(node.init_value, indent + 1)

def run_test():
    code = """
    let global_var : int = 5;
    
    #include-begin "fake_lib.nep"
    #compiler-begin
    <define-token name="MY_OPERATOR" regex="=>"/>
    #compiler-end
    let inner_var : string = "merhaba";
    #include-end
    
    async func do_task() {
        let result : int = 10;
    }
    """
    
    print("--- 1. LEXER ÇIKTISI ---")
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    for t in tokens:
        print(f"[{t.line}] {t.type}: {t.value}")
        
        
    print("\n--- 2. PARSER VE AST ÇIKTISI ---")
    parser = Parser(tokens)
    ast_root = parser.parse()
    dump_ast(ast_root)
    
    print("\n--- 3. KAPSAM (SCOPE) KAÇAĞI KONTROLÜ ---")
    stack_len = len(parser.scope_stack)
    is_safe = (stack_len == 1)
    print(f"Parser scope stack uzunluğu: {stack_len} (Beklenen: 1)")
    if is_safe:
        print("BAŞARILI: Yabancı kurallar (fake_lib.nep) dışarı sızmadı. Global kapsama geri dönüldü.")
        print(f"Global Scope Data: {parser.scope_stack[0]}")
    else:
        print("BAŞARISIZ: Kapsam Sızıntısı (Leak) var!")

if __name__ == "__main__":
    run_test()
