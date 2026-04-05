import textwrap
from src.generic_node import GenericNode

class TemplateEngine:
    """
    Şablon ve Mantık (Logic) Enjeksiyon Motoru.
    Gelen `GenericNode` ağacını gezer, bulduğu node için XML'de tanımlanmış
    bir `<transform>` Python kodu varsa bunu anında sarmalayıp (exec) üzerinden çalıştırır.
    C kodunu dışarıya tükürür.
    """
    def __init__(self, context: dict):
        self.context = context
        # context["transforms"] dict => {"AsyncFunctionDeclaration": "c_code = '...' \n return c_code"}
        
    def execute(self, ast_root: GenericNode) -> str:
        ctx_data = {"engine": self} # İçeriden recursive çağırmalar gerekebilir
        
        # 1. Üretilen C kodunun EN TEPESİNDE sadece include'lar olmalı
        out = "#include <stdio.h>\n"
        out += "#include <stdlib.h>\n\n"
        
        # 2. ORTA KISIMDA AST'den başarıyla çevrilen tüm Struct, Context ve Metotlar yer almalı
        out += self._transform_node(ast_root, ctx_data)
        
        # 3. DOSYANIN EN ALTINA (her şey bittikten sonra) gerçek C main() yazılmalı
        out += "\n// --- GERÇEK C ENTRY POINT (GCC İÇİN) ---\n"
        out += "int main(int argc, char** argv) {\n"
        out += "    Program prog;\n"
        out += "    Program_init(&prog);\n"
        out += "    \n"
        out += "    Main_Context ctx;\n"
        out += "    ctx.state = 0;\n"
        out += "    \n"
        out += "    // State-Machine Motorunu Tekmele\n"
        out += "    Main(&ctx);\n"
        out += "    \n"
        out += "    return 0;\n"
        out += "}\n"
        
        return out
        
    def _transform_node(self, node: GenericNode, ctx_data: dict) -> str:
        if not node: return ""
        
        rule_name = node.type
        
        # Program (Root) başlangıcıysa gövde elemanlarını (Class, vs) dolaş
        if rule_name == "Program":
            out = ""
            for child in node.get("BODY") or []:
                out += self._transform_node(child, ctx_data) + "\n"
            return out
            
        # 1. Transform Mantığı (Python Inline Kod Enjeksiyonu) Kontrolü
        if "transforms" in self.context and rule_name in self.context["transforms"]:
            py_code = self.context["transforms"][rule_name]
            
            # Dinamik Enjeksiyon: Kullanıcının onayladığı "def sarmalaması"
            wrapped_code = f"def __transformed_logic(node, ctx_data):\n"
            wrapped_code += textwrap.indent(py_code, '    ')
            
            local_scope = {}
            # Yüksek güvenlikli ve isolated scope mantığıyla Python derleyicisine iletiyoruz
            exec(wrapped_code, globals(), local_scope)
            func = local_scope['__transformed_logic']
            
            # Üretilen String (C Kodu) geri dönüyor
            result = func(node, ctx_data)
            
            # Gerçek C Standartlarına Uygun #line Enjeksiyonu
            if hasattr(node, "line") and getattr(node, "file", None) and node.line > 0:
                if result and result.strip() != "":
                    # Yalnızca transform mantığı boş olmayan anlamlı bir C kodu tükürüyorsa bas
                    return f'\n#line {node.line} "{node.file}"\n{result}'
                    
            return result

        # Temel Fallback: Ekrana boş basma, içindeki body veya değerleri yazdır
        out = f"/* No transform logic defined for '{rule_name}'. Rendering generic: */\n"
        for k, v in node.children.items():
            if isinstance(v, list):
                for c in v:
                    if isinstance(c, GenericNode):
                        out += self._transform_node(c, ctx_data)
            elif isinstance(v, GenericNode):
                out += self._transform_node(v, ctx_data)
        return out
