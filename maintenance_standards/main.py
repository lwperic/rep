import os
from pathlib import Path
from dotenv import load_dotenv
import gradio as gr
from loguru import logger

from backend.config import setup_logging, settings
from backend.core.document_manager.uploader import DocumentUploader

def init():
    """初始化应用"""
    # 加载环境变量
    load_dotenv()
    
    # 初始化日志
    setup_logging()
    
    # 创建必要的目录
    os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(settings.LOG_PATH, exist_ok=True)

def handle_document_upload(file):
    """处理文档上传"""
    try:
        if file is None:
            return "请选择要上传的文件"
            
        filename = file.name
        content = file.read()
        
        uploader = DocumentUploader()
        document = uploader.upload(content, filename)
        
        return f"文档上传成功！\n保存路径：{document.file_path}\n文档ID：{document.id}"
        
    except Exception as e:
        logger.error(f"文档上传失败：{str(e)}")
        return f"文档上传失败：{str(e)}"

def create_app():
    """创建Gradio应用"""
    # 创建界面
    with gr.Blocks(title="维标管理工具") as app:
        gr.Markdown("# 维标管理工具")
        
        with gr.Tab("文档管理"):
            with gr.Column():
                gr.Markdown("## 文档上传")
                file_input = gr.File(label="选择文档")
                upload_button = gr.Button("上传")
                result = gr.Textbox(label="上传结果")
                
                upload_button.click(
                    fn=handle_document_upload,
                    inputs=[file_input],
                    outputs=[result]
                )
        
        return app

def main():
    """主程序入口"""
    try:
        # 初始化
        init()
        logger.info("Starting maintenance standards application...")
        
        # 创建应用
        app = create_app()
        
        # 启动应用
        app.launch(
            server_name=settings.HOST,
            server_port=settings.PORT,
            show_error=settings.DEBUG
        )
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise

if __name__ == "__main__":
    main()