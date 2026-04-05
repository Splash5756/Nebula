import sys
from src.lexer import Lexer
from src.parser import Parser
from src.semantic import SemanticAnalyzer
from src.codegen import CodeGen
from src.preprocessor import Preprocessor, MetaScanner

def run_nebula_compiler(entry_file_path: str):
    print("============================================")
    print("      NEBULA (nep:pl) BOOTSTRAPPED COMPILER ")
    print("============================================\n")
    
    print("[1/5] Preprocessor (Ön-İşlemci) Dosyaları Düzleştiriyor...")
    preprocessor = Preprocessor(base_dir=".")
    
    try:
        flat_code = preprocessor.process_file(entry_file_path)
    except Exception as e:
        print(f"HATA: {e}")
        return
        
    print("[2/5] Meta-Scanner Modifiye Kalkanlarını ve Kuralları Okuyor...")
    scanner = MetaScanner()
    context = scanner.scan(flat_code)
    print(f"  -> Yüklenen Resmi Paketler (Modifiers): {context['modifiers']}")
    print(f"  -> Yüklenen Dış Hedef Diller: {context['target_langs']}")
    print(f"  -> Bootstrapped Token Kuralları ({len(context['tokens'])} adet) başarıyla alındı.")
    
    print("\n[3/5] Lexer (Jetonlaştırıcı) çalışıyor...")
    lexer = Lexer(flat_code)
    tokens = lexer.tokenize()
    print(f"  -> Toplam {len(tokens)} jeton hafızaya alındı.")
    
    print("\n[4/5] Parser & Semantic Analyzer Devrede...")
    parser = Parser(tokens)
    try:
        ast_root = parser.parse()
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast_root)
        print("  -> Recursion ve Global Değişken (Race Condition) Riskleri YOK.")
    except Exception as e:
        print(f"  -> SEMANTİK HATA: {e}")
        return
        
    print("\n[5/5] C Code Generator (Transpilation) Başlıyor...")
    codegen = CodeGen(context)
    h_code, c_code = codegen.generate(ast_root)
    
    print("\n---------------- OUTPUT (out.h) ----------------")
    print(h_code)
    print("\n---------------- OUTPUT (out.c) ----------------")
    print(c_code)
    print("------------------------------------------------\n")
    print("BOOTSTRAPPING BAŞARILI: Kendi kurallarını diskten okuyan dinamik mimari çalışıyor!")

if __name__ == "__main__":
    # Eğer argüman verilmemişse varsayılan test dosyasını aç
    if len(sys.argv) > 1:
        entry_file = sys.argv[1]
    else:
        entry_file = "test_user_code.nep"
    
    run_nebula_compiler(entry_file)
