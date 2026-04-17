"""
MiniMax Token Plan 用量查询插件
响应 /用量 [图片] 命令，查询 MiniMax API 额度并展示
"""

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import AstrBotConfig, logger
from astrbot.core.message.components import Image

from .api import MiniMaxAPI, QueryError
from .config import ConfigManager
from .parser import DataParser
from .draw import draw_quota_image


@register("astrbot_plugin_minimax_alert", "MiniMax_Alert", "查询 MiniMax Token Plan API 用量信息", "v1.4.0")
class MiniMaxAlertPlugin(Star):
    """MiniMax 额度查询插件主类"""

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self._config_manager = ConfigManager(config)
        self._api = MiniMaxAPI()
        self._parser = DataParser(
            show_year=self._config_manager.get_show_year(),
            show_first_model_only=self._config_manager.get_show_first_model_only()
        )

    async def initialize(self):
        """插件初始化"""
        await self._api.initialize()

    # ------------------- 内部方法 -------------------

    def _check_whitelist(self, event: AstrMessageEvent) -> bool:
        """检查用户是否在白名单中"""
        user_sid = str(event.session_id)
        whitelist_manager = self._config_manager.get_whitelist()
        return whitelist_manager.check_whitelist(user_sid)

    def _use_image_mode(self, event: AstrMessageEvent) -> bool:
        """判断是否使用图片模式"""
        return "图片" in event.message_str

    # ------------------- 指令处理 -------------------

    @filter.command("用量")
    async def query_quota(self, event: AstrMessageEvent):
        """查询配额命令 /用量 [图片]"""
        # 白名单校验
        if not self._check_whitelist(event):
            yield event.plain_result("⚠️ 该功能仅对白名单用户开放")
            return

        # 获取配置
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

            # 图片模式：渲染图片，失败时降级为文字
            if use_image:
                try:
                    draw_data = self._parser.parse_quota_data_for_draw(quota_data)
                    img_bytes = draw_quota_image(
                        plan_name=draw_data["plan_name"],
                        model_cards=draw_data["model_cards"],
                        period_text=draw_data["period_text"],
                        week_period_text=draw_data["week_period_text"],
                        reset_text=draw_data["reset_text"],
                    )
                    yield event.chain_result([Image.fromBytes(img_bytes)])
                    logger.info("图片渲染成功")
                except Exception as e:
                    logger.error(f"图片渲染失败: {str(e)}")
                    result = self._parser.parse_quota_data(quota_data)
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
        """插件销毁"""
        await self._api.terminate()
