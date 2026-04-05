import sys
import os
import subprocess

from src.preprocessor import Preprocessor, MetaScanner
from src.lexer import Lexer
from src.parser import Parser
from src.template_engine import TemplateEngine

def run_nebula(entry_file_path: str):
    if not entry_file_path.endswith(".neb"):
        print(f"Fatal Error: Lutfen gecerli bir Nebula dosyasi (.neb) veriniz. Gecersiz form: {entry_file_path}")
        return
        
    print(f"Nebula Compiler v0.2 - Building {entry_file_path}...")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    preprocessor = Preprocessor(base_dir=base_dir)
    
    try:
        flat_code = preprocessor.process_file(entry_file_path)
    except Exception as e:
        print(f"Build Failed! Preprocessor Error: {e}")
        return
        
    scanner = MetaScanner()
    context, clean_code = scanner.scan(flat_code)
    
    lexer = Lexer(clean_code, context["tokens"])
    tokens = lexer.tokenize()
    
    parser = Parser(tokens, context["rules"])
    try:
        ast_root = parser.parse()
    except Exception as e:
        print(f"Build Failed! Parser Error: {e}")
        return
    
    engine = TemplateEngine(context)
    c_code = engine.execute(ast_root)
    
    build_dir = os.path.join(base_dir, "build")
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)
        
    out_c_path = os.path.join(build_dir, "output.c")
    out_exe_path = os.path.join(build_dir, "program.exe")
    
    with open(out_c_path, 'w', encoding='utf-8') as f:
        f.write(c_code)
        
    print(f"Build Successful! Output saved to build/output.c")
    
    # GCC ile otomatik derleme
    print(f"Compiling with GCC...")
    try:
        compile_proc = subprocess.run(["gcc", out_c_path, "-o", out_exe_path], capture_output=True, text=True)
        if compile_proc.returncode != 0:
            print("GCC Compilation Failed!")
            print(compile_proc.stderr)
            return
            
        print("Compilation Successful! Executing program...\n")
        print("--- PROGRAM OUTPUT ---")
        exec_proc = subprocess.run([out_exe_path], capture_output=True, text=True)
        print(exec_proc.stdout)
        if exec_proc.stderr:
             print(exec_proc.stderr)
        print("----------------------")
    except FileNotFoundError:
        print("[Uyarı] GCC sisteminizde bulunamadı (Path'e ekli değil). C kodunuz 'build/output.c' dizininde başarıyla üretildi. Kendi C derleyicinizle derleyebilirsiniz.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        entry_file = sys.argv[1]
    else:
        entry_file = "tests/hello_world.neb"
    run_nebula(entry_file)
