import os
import re

class PreprocessorError(Exception):
    pass

class Preprocessor:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.visited_files = set()
        
        # Sadece basit tırnak içi include algılayıcısı: örn: include "lib.nep"
        self.include_pattern = re.compile(r'^\s*include\s+"([^"]+)"')
        self.compiler_begin_pattern = re.compile(r'^\s*#compiler-begin')

    def process_file(self, filename: str) -> str:
        """Dosyayı okur, include'ları öz yineli(recursive) olarak çözer ve devasa tek bir kod bloğuna döndürür."""
        abs_path = os.path.abspath(os.path.join(self.base_dir, filename))
        
        if abs_path in self.visited_files:
            # GÜVENLİK DUVARI 1: DÖNGÜSEL BAĞIMLILIK KORUMASI (Circular Dependency Guard)
            raise PreprocessorError(f"Fatal Error: Circular Dependency tespit edildi! Dosya daha önce include edildi: {filename}")
            
        self.visited_files.add(abs_path)
        
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except FileNotFoundError:
            raise PreprocessorError(f"Fatal Error: Include edilecek dosya bulunamadı: {filename}")

        output_lines = []
        full_content = "".join(lines)
        
        # Modifier etiketi var mı kontrol et (<modifier name="..." />)
        has_modifier = '<modifier' in full_content
        has_include = any(self.include_pattern.match(line) for line in lines)
                
        # GÜVENLİK DUVARI 2: MODİFİYE EDİCİ İZOLASYONU (Modifier Isolation)
        if has_modifier and has_include:
            raise PreprocessorError(
                f"Fail-Fast Error: Modifier Isolation ihlali! '{filename}' dosyası "
                f"resmi bir dil genişletme paketi (Modifier Etiketi taşıyor) "
                f"fakat başka bir dosyayı include etmeye çalışıyor."
            )

        # Dönüştürme turu
        for line in lines:
            inc_match = self.include_pattern.match(line)
            if inc_match:
                target_file = inc_match.group(1)
                
                # Include başlama bayrağını at (Parser Kapsamı için)
                output_lines.append(f'\n#include-begin "{target_file}"')
                
                # Öz yineli olarak içteki dosyayı parseleyip yapıştır
                inner_content = self.process_file(target_file)
                output_lines.append(inner_content)
                
                # Include bitiş bayrağını at
                output_lines.append(f'\n#include-end')
            else:
                output_lines.append(line.rstrip("\n"))
                
        # İçinden çıkarken listeden silmiyoruz çünkü bir dosya projede sadece 1 kez include edilsin
        return "\n".join(output_lines)


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
            "target_langs": []
        }
        
    def scan(self, flat_code: str) -> dict:
        # Compiler bloklarını bul
        # Regex: #compiler-begin'den #compiler-end'e kadar (non-greedy)
        block_pattern = re.compile(r'#compiler-begin(.*?)#compiler-end', re.DOTALL)
        
        blocks = block_pattern.findall(flat_code)
        
        modifier_pattern = re.compile(r'<modifier\s+name="([^"]+)"')
        token_pattern = re.compile(r'<define-token\s+name="([^"]+)"\s+regex="([^"]+)"\s*/>')
        rule_pattern = re.compile(r'<rule\s+name="([^"]+)".*?/>')
        target_lang_pattern = re.compile(r'<use\s+target-lang="([^"]+)"\s*/>')
        
        for block in blocks:
            # Modifiers
            for m_match in modifier_pattern.finditer(block):
                self.compiler_context["modifiers"].append(m_match.group(1))
                
            # Token tanımlarını topla
            for t_match in token_pattern.finditer(block):
                self.compiler_context["tokens"].append({
                    "name": t_match.group(1),
                    "regex": t_match.group(2)
                })
                
            # Öncelikli kuralları topla (precedence vb.)
            for r_match in rule_pattern.finditer(block):
                self.compiler_context["rules"].append({
                    "name": r_match.group(1)
                })
                
            # Yabancı dil/C-API (Target-Lang) eklentilerini topla
            for tl_match in target_lang_pattern.finditer(block):
                self.compiler_context["target_langs"].append(tl_match.group(1))
                
        return self.compiler_context
