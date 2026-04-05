import os
import re

class PreprocessorError(Exception):
    pass

class Preprocessor:
    def __init__(self, base_dir: str, global_include_paths: list = None):
        self.base_dir = base_dir
        self.visited_files = set()
        
        # GCC/Clang tarzı Standart Arama Yolları
        if global_include_paths is None:
            self.global_include_paths = [
                base_dir,
                os.path.join(base_dir, "core_packages")
            ]
        else:
            self.global_include_paths = global_include_paths
            
        self.include_pattern = re.compile(r'^\s*include\s+"([^"]+)"')
        self.compiler_begin_pattern = re.compile(r'^\s*#compiler-begin')

    def _resolve_include(self, target_file: str, current_file_dir: str) -> str:
        paths_tried = []
        
        # 1. Relative Resolution (Mevcut dosya ile aynı dizine bak)
        if current_file_dir:
            candidate = os.path.abspath(os.path.join(current_file_dir, target_file))
            paths_tried.append(candidate)
            if os.path.exists(candidate) and os.path.isfile(candidate):
                return candidate
                
        # 2. Global Yollar (Global Include Paths)
        for g_path in self.global_include_paths:
            candidate = os.path.abspath(os.path.join(g_path, target_file))
            paths_tried.append(candidate)
            if os.path.exists(candidate) and os.path.isfile(candidate):
                return candidate
                
        # Bulunamadıysa gelişmiş path dökümü fırlat
        paths_str = "\n  - ".join(paths_tried)
        raise PreprocessorError(f"Fatal Error: '{target_file}' adli dosya bulunamadi! Aranan yollar:\n  - {paths_str}")

    def process_file(self, filename: str, current_file_dir: str = None) -> str:
        # Eğer ilk dosyaysa (current_file_dir None ise) base_dir referans alınır.
        # İlk girişten önce absolute verilmediyse relative çözeriz.
        if abs_path := self._resolve_include(filename, current_file_dir or self.base_dir):
            if abs_path in self.visited_files:
                raise PreprocessorError(f"Fatal Error: Circular Dependency tespit edildi! Dosya daha önce include edildi: {abs_path}")
        else:
            raise PreprocessorError("Bilinmeyen cozunurluk hatasi.")
            
        self.visited_files.add(abs_path)
        
        with open(abs_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        is_root = current_file_dir is None
        output_lines = []
        full_content = "".join(lines)
        
        has_modifier = '<modifier' in full_content
        has_include = any(self.include_pattern.match(line) for line in lines)
                
        if has_modifier and has_include:
            raise PreprocessorError(
                f"Fail-Fast Error: Modifier Isolation ihlali! '{filename}' dosyası "
                f"resmi bir dil genişletme paketi (Modifier Etiketi taşıyor) "
                f"fakat başka bir dosyayı include etmeye çalışıyor."
            )

        this_dir = os.path.dirname(abs_path)

        for line in lines:
            inc_match = self.include_pattern.match(line)
            if inc_match:
                target_file = inc_match.group(1)
                
                # Relatif Context'i içe doğru akıtıyoruz
                inner_content = self.process_file(target_file, this_dir)
                
                # Orijinal newline dizilimini bozmamak için her şeyi TEK satırda (inline) sarıyoruz
                output_lines.append(f'#include-begin "{target_file}" ' + inner_content + f' #include-end')
            else:
                output_lines.append(line.rstrip("\n"))
                
        full_result = "\n".join(output_lines)
        if is_root:
            return f'#include-begin "{filename}" ' + full_result + f' #include-end'
        return full_result



class MetaScanner:
    """
    GÜVENLİK DUVARI 3: META-TARAYICI ÇIKTISI
    Parser, kodu okumadan ÖNCE bu flat (düzleştirilmiş) kod üzerinde koşar, 
    XML/HTML tabanlı derleyici konfigürasyonlarını toplar.
    """
    def __init__(self):
        self.compiler_context = {
            "modifiers": [],
            "tokens": [],
            "rules": [],
            "target_langs": [],
            "transforms": {}
        }
        
    def scan(self, flat_code: str) -> tuple[dict, str]:
        # Compiler bloklarını bul
        # Regex: #compiler-begin'den #compiler-end'e kadar (non-greedy)
        block_pattern = re.compile(r'#compiler-begin(.*?)#compiler-end', re.DOTALL)
        
        def repl(m): return '\n' * m.group(0).count('\n')
        
        blocks = block_pattern.findall(flat_code)
        
        modifier_pattern = re.compile(r'<modifier\s+name="([^"]+)"')
        token_pattern = re.compile(r'<define-token\s+name="([^"]+)"\s+regex=(?:"([^"]+)"|\'([^\']+)\')\s*/>')
        rule_pattern = re.compile(r'<rule\s+name="([^"]+)"\s+pattern="([^"]+)"\s*/>')
        target_lang_pattern = re.compile(r'<use\s+target-lang="([^"]+)"\s*/>')
        transform_pattern = re.compile(r'<transform\s+node="([^"]+)">(.*?)</transform>', re.DOTALL)
        logic_pattern = re.compile(r'<logic>(.*?)</logic>', re.DOTALL)
        
        for block in blocks:
            # Modifiers
            for m_match in modifier_pattern.finditer(block):
                self.compiler_context["modifiers"].append(m_match.group(1))
                
            # Token tanımlarını topla
            for t_match in token_pattern.finditer(block):
                self.compiler_context["tokens"].append({
                    "name": t_match.group(1),
                    "regex": t_match.group(2) or t_match.group(3)
                })
                
            # Öncelikli kuralları topla (precedence vb.)
            # Karışık kuralları topla ve pattern yakala
            for r_match in rule_pattern.finditer(block):
                self.compiler_context["rules"].append({
                    "name": r_match.group(1),
                    "pattern": r_match.group(2)
                })
                
            # Yabancı dil/C-API (Target-Lang) eklentilerini topla
            for tl_match in target_lang_pattern.finditer(block):
                self.compiler_context["target_langs"].append(tl_match.group(1))
                
            # Transform Enjeksiyonlarını topla
            for tr_match in transform_pattern.finditer(block):
                node_name = tr_match.group(1)
                content = tr_match.group(2)
                l_match = logic_pattern.search(content)
                if l_match:
                    self.compiler_context["transforms"][node_name] = l_match.group(1).strip()
                
        # Lexer'in cope batmamasi icin XML bloklari koda dahil edilmesin (AMA line sayisi korunsun)
        clean_code = block_pattern.sub(repl, flat_code)
        clean_code = modifier_pattern.sub(repl, clean_code)
                
        return self.compiler_context, clean_code
