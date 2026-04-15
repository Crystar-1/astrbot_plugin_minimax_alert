import asyncio
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from typing import Optional

from astrbot.api import logger

from .api import MiniMaxAPI, QueryError
from .parser import DataParser
from .config import ConfigManager
from .whitelist import WhitelistManager


class MonitorState(Enum):
    STOPPED = "stopped"
    LOCKED = "locked"
    TRIGGERED = "triggered"


@dataclass
class MonitorConfig:
    threshold: int
    default_interval: int
    min_interval: int


QUOTA_ALERT_MESSAGE = """⚠️ MiniMax 用量报警
当前5小时使用量已达 {current_percent:.1f}%
阈值: {threshold}%
请及时关注！"""


class QuotaMonitor:
    def __init__(
        self,
        api: MiniMaxAPI,
        parser: DataParser,
        context,
        config_manager: ConfigManager,
        whitelist_manager: WhitelistManager,
    ):
        self._api = api
        self._parser = parser
        self._context = context
        self._config_manager = config_manager
        self._whitelist_manager = whitelist_manager
        self._state = MonitorState.STOPPED
        self._threshold: int = 0
        self._last_check_time: Optional[datetime] = None
        self._last_check_value: Optional[float] = None
        self._task: Optional[asyncio.Task] = None

    @property
    def state(self) -> MonitorState:
        return self._state

    def get_status(self) -> dict:
        return {
            "state": self._state.value,
            "threshold": self._threshold,
            "last_check_time": self._last_check_time.isoformat() if self._last_check_time else None,
            "last_check_value": self._last_check_value,
        }

    def _should_notify(self, current_percent: float) -> bool:
        return current_percent >= self._threshold

    async def _send_alert(self, current_percent: float) -> None:
        whitelist = self._whitelist_manager.get_whitelist()
        if not whitelist:
            logger.warning("白名单为空，无法发送报警通知")
            return

        message = QUOTA_ALERT_MESSAGE.format(
            current_percent=current_percent,
            threshold=self._threshold,
        )

        for sid in whitelist:
            try:
                chain = [{"type": "plain", "text": message}]
                await self._context.send_message(sid, chain)
                logger.info(f"报警通知已发送给 {sid}")
            except Exception as e:
                logger.error(f"发送报警通知给 {sid} 失败: {str(e)}")

    async def _check_and_notify(self) -> None:
        try:
            current_percent = await self._get_current_percent()
            self._last_check_time = datetime.now()
            self._last_check_value = current_percent

            should_notify = self._should_notify(current_percent)

            if self._state == MonitorState.LOCKED and should_notify:
                await self._send_alert(current_percent)
                self._state = MonitorState.TRIGGERED
                logger.info(f"用量超过阈值 {self._threshold}%，已触发报警，切换到TRIGGERED状态")
            elif self._state == MonitorState.TRIGGERED and not should_notify:
                self._state = MonitorState.LOCKED
                logger.info(f"用量降至阈值以下，重新ARM")
        except QueryError as e:
            logger.error(f"检查配额失败: {str(e)}")
        except Exception as e:
            logger.error(f"检查通知异常: {str(e)}")

    async def _run_loop(self) -> None:
        while True:
            try:
                interval = self._calculate_interval()
                await asyncio.sleep(interval * 60)
                await self._check_and_notify()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"监控循环异常: {str(e)}，5分钟后重试")
                await asyncio.sleep(5 * 60)

    async def stop(self) -> str:
        if self._state == MonitorState.STOPPED:
            return "监控未在运行"

        if self._task:
            self._task.cancel()
            self._task = None

        self._state = MonitorState.STOPPED
        logger.info("用量监控已停止")
        return "用量监控已停止"

    async def start(self, threshold: int) -> str:
        if self._state != MonitorState.STOPPED:
            return f"监控已在运行（当前状态：{self._state.value}）"

        self._threshold = threshold
        self._state = MonitorState.LOCKED
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"用量监控已启动，阈值：{threshold}%")
        return f"用量监控已启动，阈值：{threshold}%"

    def _calculate_interval(self) -> int:
        if self._last_check_value is None:
            return self._config_manager.get_default_interval()

        diff = abs(self._last_check_value - self._threshold)

        if self._last_check_value >= self._threshold:
            return self._config_manager.get_min_interval()

        if diff <= 5:
            ratio = diff / 5
            return int(
                self._config_manager.get_min_interval()
                + (self._config_manager.get_default_interval() - self._config_manager.get_min_interval()) * ratio
            )

        return self._config_manager.get_default_interval()

    async def _get_current_percent(self) -> float:
        api_key = self._config_manager.get_api_key()
        region = self._config_manager.get_region()
        group_id = self._config_manager.get_group_id()

        quota_data = await self._api.fetch_quota(api_key, region, group_id)
        draw_data = self._parser.parse_quota_data_for_draw(quota_data)
        model_cards = draw_data.get("model_cards", [])

        if not model_cards:
            return 0.0

        intv_used = model_cards[0].get("intv_used", 0)
        intv_total = model_cards[0].get("intv_total", 0)

        if intv_total == 0:
            return 0.0

        return (intv_used / intv_total) * 100
