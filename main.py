from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import AstrBotConfig, logger

from .api import MiniMaxAPI, QueryError
from .config import ConfigManager
from .parser import DataParser
from .whitelist import WhitelistManager
from .renderer import get_renderer, PILLYMD_AVAILABLE


@register("astrbot_plugin_minimax_alert", "MiniMax_Alert", "查询 MiniMax Token Plan API 用量信息", "v1.3.1")
class MiniMaxAlertPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self._config_manager = ConfigManager(config)
        self._api = MiniMaxAPI()
        self._parser = DataParser(
            show_year=self._config_manager.get_show_year(),
            show_first_model_only=self._config_manager.get_show_first_model_only()
        )
    
    async def initialize(self):
        await self._api.initialize()
    
    def _check_whitelist(self, event: AstrMessageEvent) -> bool:
        """
        检查用户是否在白名单中

        Args:
            event: 消息事件

        Returns:
            True 如果用户允许访问
        """
        user_sid = str(event.session_id)
        whitelist_manager = self._config_manager.get_whitelist()
        return whitelist_manager.check_whitelist(user_sid)
    
    def _use_image_mode(self, event: AstrMessageEvent) -> bool:
        """检测是否使用图片模式"""
        msg = event.message_str
        return "图片" in msg
    
    @filter.command("用量")
    async def query_quota(self, event: AstrMessageEvent):
        """查询配额命令"""
        if not self._check_whitelist(event):
            yield event.plain_result("⚠️ 该功能仅对白名单用户开放")
            return
        
        api_key = self._config_manager.get_api_key()
        region = self._config_manager.get_region()
        group_id = self._config_manager.get_group_id()
        
        if not api_key:
            logger.warning("用户未配置 API Key")
            yield event.plain_result("⚠️ 请先在插件设置中配置 MiniMax API Key")
            return
        
        use_image = self._use_image_mode(event)
        
        try:
            logger.info(f"开始查询用量: region={region}, group_id={group_id}, use_image={use_image}")
            quota_data = await self._api.fetch_quota(api_key, region, group_id)
            
            if use_image:
                result = self._parser.parse_quota_data_markdown(quota_data)
                if not PILLYMD_AVAILABLE:
                    yield event.plain_result("⚠️ 图片渲染功能未启用，请安装 pillowmd 依赖")
                    return
                
                try:
                    renderer = get_renderer()
                    img_io = renderer.render_to_bytesio(result)
                    yield event.image_result(img_io, "image/png")
                    logger.info("图片渲染成功")
                except Exception as e:
                    logger.error(f"图片渲染失败: {str(e)}")
                    yield event.plain_result(f"⚠️ 图片渲染失败：{str(e)}\n\n{result}")
            else:
                result = self._parser.parse_quota_data(quota_data)
                yield event.plain_result(result)
                
        except ValueError as e:
            logger.error(f"配置错误: {str(e)}")
            yield event.plain_result(f"⚠️ 配置错误：{str(e)}")
        except QueryError as e:
            logger.error(f"业务查询错误: {str(e)}")
            yield event.plain_result(f"❌ {str(e)}")
        except Exception as e:
            logger.error(f"网络错误: {str(e)}")
            yield event.plain_result(f"❌ 网络错误：{str(e)}")
    
    async def terminate(self):
        await self._api.terminate()
