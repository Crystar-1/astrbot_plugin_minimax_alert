from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import AstrBotConfig, logger
from astrbot.core.message.components import Image

from .api import MiniMaxAPI, QueryError
from .config import ConfigManager
from .parser import DataParser
from .whitelist import WhitelistManager
from .draw import draw_quota_image
from .monitor import QuotaMonitor, MonitorState


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
        self._monitor = QuotaMonitor(
            api=self._api,
            parser=self._parser,
            context=context,
            config_manager=self._config_manager,
            whitelist_manager=self._config_manager.get_whitelist()
        )
    
    async def initialize(self):
        await self._api.initialize()
    
    def _check_whitelist(self, event: AstrMessageEvent) -> bool:
        user_sid = str(event.session_id)
        whitelist_manager = self._config_manager.get_whitelist()
        return whitelist_manager.check_whitelist(user_sid)
    
    def _use_image_mode(self, event: AstrMessageEvent) -> bool:
        msg = event.message_str
        return "图片" in msg
    
    @filter.command("用量")
    async def query_quota(self, event: AstrMessageEvent):
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
    
    @filter.command("用量检测")
    async def monitor_control(self, event: AstrMessageEvent):
        """用量检测监控指令"""
        if not self._check_whitelist(event):
            yield event.plain_result("⚠️ 该功能仅对白名单用户开放")
            return
        
        msg = event.message_str.strip()
        parts = msg.split(maxsplit=1)
        sub_cmd = parts[1] if len(parts) > 1 else ""
        
        if sub_cmd == "状态":
            status = self._monitor.get_status()
            if status["state"] == "stopped":
                yield event.plain_result("📊 用量监控状态：已停止")
            else:
                state_emoji = "🔔" if status["state"] == "triggered" else "🔒"
                yield event.plain_result(
                    f"{state_emoji} 用量监控状态：运行中\n"
                    f"阈值：{status['threshold']}%\n"
                    f"上次检测：{status['last_check_time']} 使用量 {status['last_check_value']:.1f}%"
                )
        
        elif sub_cmd == "关闭":
            result = await self._monitor.stop()
            yield event.plain_result(result)
        
        elif sub_cmd:
            try:
                threshold = int(sub_cmd)
                if not (1 <= threshold <= 100):
                    raise ValueError("阈值超出范围")
                result = await self._monitor.start(threshold)
                yield event.plain_result(result)
            except ValueError:
                yield event.plain_result("⚠️ 请输入有效的阈值（1-100），如：/用量检测 80")
        else:
            yield event.plain_result(
                "📖 用量检测指令用法：\n"
                "/用量检测 80 - 启动监控，阈值80%\n"
                "/用量检测 状态 - 查看监控状态\n"
                "/用量检测 关闭 - 停止监控"
            )
    
    async def terminate(self):
        await self._api.terminate()
