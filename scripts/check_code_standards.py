#!/usr/bin/env python3
"""
代码规范检查脚本
检查HTML、CSS、JavaScript文件是否符合项目开发规范
"""

import os
import re
import sys
from pathlib import Path

class CodeStandardsChecker:
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.errors = []
        self.warnings = []
    
    def check_html_files(self):
        """检查HTML文件是否符合规范"""
        html_files = list(self.project_root.rglob("*.html"))
        
        for html_file in html_files:
            if "templates" not in str(html_file):
                continue
                
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查内联样式
                if re.search(r'<style[^>]*>', content):
                    self.errors.append(f"❌ {html_file}: 发现内联<style>标签")
                
                # 检查内联脚本（排除带src属性的script标签和type="application/json"的配置）
                script_tags = re.findall(r'<script[^>]*>.*?</script>', content, re.DOTALL)
                for script_tag in script_tags:
                    # 如果script标签没有src属性，且不是JSON配置，且有内容，则认为是内联脚本
                    if 'src=' not in script_tag and 'type="application/json"' not in script_tag and re.search(r'<script[^>]*>(?!\s*</script>)', script_tag, re.DOTALL):
                        self.errors.append(f"❌ {html_file}: 发现内联<script>标签")
                        break
                
                # 检查内联事件处理
                if re.search(r'onclick\s*=', content):
                    self.warnings.append(f"⚠️  {html_file}: 发现内联onclick事件，建议使用addEventListener")
                
                # 检查是否引用了外部CSS和JS文件
                if not re.search(r'<link[^>]*\.css', content):
                    self.warnings.append(f"⚠️  {html_file}: 未发现外部CSS文件引用")
                
                if not re.search(r'<script[^>]*\.js', content):
                    self.warnings.append(f"⚠️  {html_file}: 未发现外部JS文件引用")
                    
            except Exception as e:
                self.errors.append(f"❌ 读取文件失败 {html_file}: {e}")
    
    def check_css_files(self):
        """检查CSS文件结构"""
        css_files = list(self.project_root.rglob("*.css"))
        
        if not css_files:
            self.warnings.append("⚠️  未发现CSS文件")
            return
        
        for css_file in css_files:
            try:
                with open(css_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查CSS文件是否有内容
                if len(content.strip()) == 0:
                    self.warnings.append(f"⚠️  {css_file}: CSS文件为空")
                
                # 检查是否有内联样式混入
                if re.search(r'<style', content):
                    self.errors.append(f"❌ {css_file}: CSS文件中不应包含HTML标签")
                    
            except Exception as e:
                self.errors.append(f"❌ 读取文件失败 {css_file}: {e}")
    
    def check_js_files(self):
        """检查JavaScript文件结构"""
        js_files = list(self.project_root.rglob("*.js"))
        
        if not js_files:
            self.warnings.append("⚠️  未发现JavaScript文件")
            return
        
        for js_file in js_files:
            try:
                with open(js_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查JS文件是否有内容
                if len(content.strip()) == 0:
                    self.warnings.append(f"⚠️  {js_file}: JavaScript文件为空")
                
                # 检查是否有HTML标签混入
                if re.search(r'<script', content):
                    self.errors.append(f"❌ {js_file}: JavaScript文件中不应包含HTML标签")
                
                # 检查是否使用了现代JavaScript语法
                if 'var ' in content and 'let ' not in content and 'const ' not in content:
                    self.warnings.append(f"⚠️  {js_file}: 建议使用let/const替代var")
                
                # 检查是否有addEventListener使用
                if 'addEventListener' in content:
                    print(f"✅ {js_file}: 使用了现代事件处理方式")
                    
            except Exception as e:
                self.errors.append(f"❌ 读取文件失败 {js_file}: {e}")
    
    def check_file_structure(self):
        """检查文件结构是否符合规范"""
        static_dir = self.project_root / "visiofirm" / "static"
        templates_dir = self.project_root / "visiofirm" / "templates"
        
        # 检查static目录结构
        if not static_dir.exists():
            self.errors.append("❌ 缺少static目录")
        else:
            css_dir = static_dir / "css"
            js_dir = static_dir / "js"
            
            if not css_dir.exists():
                self.errors.append("❌ 缺少static/css目录")
            if not js_dir.exists():
                self.errors.append("❌ 缺少static/js目录")
        
        # 检查templates目录
        if not templates_dir.exists():
            self.errors.append("❌ 缺少templates目录")
    
    def check_api_design(self):
        """检查API设计是否符合RESTful规范"""
        routes_dir = self.project_root / "visiofirm" / "routes"
        
        if not routes_dir.exists():
            self.warnings.append("⚠️  未发现routes目录")
            return
        
        for route_file in routes_dir.glob("*.py"):
            try:
                with open(route_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查是否有render_template调用（应该避免）
                if 'render_template' in content:
                    self.warnings.append(f"⚠️  {route_file}: 发现render_template调用，建议使用API返回JSON")
                
                # 检查是否有jsonify使用
                if 'jsonify' in content:
                    print(f"✅ {route_file}: 使用了JSON API设计")
                
                # 检查RESTful路由设计
                if re.search(r'@bp\.route.*methods=\[.*GET.*\]', content):
                    print(f"✅ {route_file}: 使用了RESTful GET方法")
                if re.search(r'@bp\.route.*methods=\[.*POST.*\]', content):
                    print(f"✅ {route_file}: 使用了RESTful POST方法")
                if re.search(r'@bp\.route.*methods=\[.*PUT.*\]', content):
                    print(f"✅ {route_file}: 使用了RESTful PUT方法")
                if re.search(r'@bp\.route.*methods=\[.*DELETE.*\]', content):
                    print(f"✅ {route_file}: 使用了RESTful DELETE方法")
                    
            except Exception as e:
                self.errors.append(f"❌ 读取文件失败 {route_file}: {e}")
    
    def run_checks(self):
        """运行所有检查"""
        print("🔍 开始检查代码规范...")
        print("=" * 50)
        
        self.check_file_structure()
        self.check_html_files()
        self.check_css_files()
        self.check_js_files()
        self.check_api_design()
        
        print("\n📊 检查结果:")
        print("=" * 50)
        
        if self.errors:
            print(f"❌ 发现 {len(self.errors)} 个错误:")
            for error in self.errors:
                print(f"  {error}")
        
        if self.warnings:
            print(f"\n⚠️  发现 {len(self.warnings)} 个警告:")
            for warning in self.warnings:
                print(f"  {warning}")
        
        if not self.errors and not self.warnings:
            print("✅ 所有检查通过！代码符合项目规范。")
            return True
        
        if self.errors:
            print(f"\n❌ 发现 {len(self.errors)} 个错误，请修复后再提交代码。")
            return False
        
        print(f"\n⚠️  发现 {len(self.warnings)} 个警告，建议优化。")
        return True

def main():
    """主函数"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    checker = CodeStandardsChecker(project_root)
    
    success = checker.run_checks()
    
    if not success:
        sys.exit(1)
    else:
        print("\n🎉 代码规范检查完成！")

if __name__ == "__main__":
    main()
