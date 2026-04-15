import os
import io
from typing import Optional
from PIL import Image
from astrbot.api import logger


try:
    import pillowmd
    PILLYMD_AVAILABLE = True
except ImportError:
    PILLYMD_AVAILABLE = False
    logger.warning("pillowmd 未安装，图片渲染功能将不可用")


STYLE_DIR = os.path.join(os.path.dirname(__file__), "styles")
FONT_PATH = os.path.join(os.path.dirname(__file__), "DouyinSansBold.otf")
WHITE_BG_PATH = os.path.join(STYLE_DIR, "white.png")


class QuotaRenderer:
    def __init__(self):
        self._style = None
        self._initialized = False
    
    def _ensure_background(self):
        if not os.path.exists(WHITE_BG_PATH):
            os.makedirs(os.path.dirname(WHITE_BG_PATH), exist_ok=True)
            img = Image.new("RGB", (10, 10), color=(255, 255, 255))
            img.save(WHITE_BG_PATH, "PNG")
    
    def initialize(self):
        if not PILLYMD_AVAILABLE:
            raise RuntimeError("pillowmd 未安装，请运行: pip install pillowmd")
        
        try:
            self._ensure_background()
            self._style = pillowmd.LoadMarkdownStyles(STYLE_DIR)
            self._initialized = True
            logger.info("QuotaRenderer 初始化成功")
        except Exception as e:
            logger.error(f"QuotaRenderer 初始化失败: {e}")
            raise
    
    def render_to_image(self, markdown_content: str) -> bytes:
        if not self._initialized:
            self.initialize()
        
        if not PILLYMD_AVAILABLE:
            raise RuntimeError("pillowmd 未安装")
        
        try:
            result_img = self._style.Render(markdown_content)
            
            if isinstance(result_img, Image.Image):
                img_bytes = io.BytesIO()
                result_img.save(img_bytes, format="PNG", quality=95)
                return img_bytes.getvalue()
            elif isinstance(result_img, bytes):
                return result_img
            else:
                raise ValueError(f"未知的渲染结果类型: {type(result_img)}")
        
        except Exception as e:
            logger.error(f"Markdown 渲染失败: {e}")
            raise
    
    def render_to_bytesio(self, markdown_content: str) -> io.BytesIO:
        img_bytes = self.render_to_image(markdown_content)
        return io.BytesIO(img_bytes)


_renderer_instance: Optional[QuotaRenderer] = None


def get_renderer() -> QuotaRenderer:
    global _renderer_instance
    if _renderer_instance is None:
        _renderer_instance = QuotaRenderer()
    return _renderer_instance
