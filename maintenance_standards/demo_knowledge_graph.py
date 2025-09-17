#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tempfile
from pathlib import Path
import gradio as gr

from backend.core.document_manager.uploader import DocumentUploader
from backend.core.knowledge_graph.extractor import KnowledgeExtractor
from backend.core.knowledge_graph.neo4j_manager import Neo4jManager

class DocumentManager:
    """Document Manager"""
    def __init__(self):
        """Initialize document manager"""
        self.temp_dir = tempfile.mkdtemp()
        self.uploader = DocumentUploader()
        
    def validate_files(self, files):
        """Validate uploaded files"""
        if not files:
            return False
            
        for file in files:
            if not file.name.lower().endswith(('.doc', '.docx')):
                return False
        return True
        
    def save_files(self, files):
        """Save files to temporary directory"""
        temp_paths = []
        for file in files:
            temp_path = os.path.join(self.temp_dir, file.name)
            with open(temp_path, 'wb') as f:
                f.write(file.read())
            temp_paths.append(temp_path)
        return temp_paths

class KnowledgeGraphUI:
    """Knowledge Graph UI"""
    def __init__(self):
        """Initialize UI"""
        self.doc_manager = DocumentManager()
        self.extractor = KnowledgeExtractor()
        self.neo4j = Neo4jManager()
        
    def extract_and_save(self, files, selected_files):
        """Extract and save knowledge from selected documents"""
        if not self.doc_manager.validate_files(files):
            return "请上传Word文档（.doc或.docx格式）"
            
        if not selected_files:
            return "请选择至少一个文档进行处理"
            
        try:
            temp_paths = self.doc_manager.save_files(files)
            # 根据选中的文件名获取对应的路径
            selected_paths = []
            for file in files:
                if file.name in selected_files:
                    temp_path = os.path.join(self.temp_dir, file.name)
                    selected_paths.append(temp_path)
            
            for path in selected_paths:
                knowledge = self.extractor.extract(path)
                self.neo4j.save(knowledge)
                
            return f"成功处理{len(selected_paths)}个文档"
            
        except Exception as e:
            return f"处理文档时出错: {str(e)}"
            
    def build_ui(self):
        """Build Gradio interface"""
        with gr.Blocks(title="维修知识图谱管理系统", theme=gr.themes.Base()) as interface:
            gr.Markdown("# 维修知识图谱管理系统")
            
            with gr.Column(scale=1):
                # 文档上传区域
                with gr.Group():
                    gr.Markdown("### 1. 文档上传")
                    file_output = gr.File(
                        label="上传维修文档",
                        file_types=[".doc", ".docx"],
                        file_count="multiple"
                    )
                
                # 文档选择区域
                with gr.Group():
                    gr.Markdown("### 2. 文档选择")
                    doc_selection = gr.CheckboxGroup(
                        label="选择要处理的文档",
                        choices=[],
                        value=[],
                        container=True,
                        interactive=True,
                        elem_classes="checkbox-list"
                    )
                
                # 处理按钮和结果区域
                with gr.Group():
                    gr.Markdown("### 3. 处理文档")
                    process_btn = gr.Button("处理选中文档", variant="primary", size="lg")
                    result_text = gr.Textbox(label="处理结果", container=True)
            
            # 更新文档列表
            def update_doc_list(files):
                if not files:
                    return gr.CheckboxGroup.update(choices=[], value=[])
                # 使用文件名作为选项
                choices = [file.name for file in files]
                return gr.CheckboxGroup.update(choices=choices, value=[])
            
            file_output.change(
                fn=update_doc_list,
                inputs=[file_output],
                outputs=[doc_selection]
            )
            
            # 处理文档
            process_btn.click(
                fn=lambda f, s: self.extract_and_save(f, s),
                inputs=[file_output, doc_selection],
                outputs=[result_text]
            )
            
        return interface

if __name__ == "__main__":
    # Start the application
    ui = KnowledgeGraphUI()
    interface = ui.build_ui()
    interface.launch(
        server_name="0.0.0.0",
        show_api=False,
        share=True,
        favicon_path=None
    )