from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from .api import QueryError
from astrbot.api import logger


# 中国时区偏移量（UTC+8）
CHINA_TIMEZONE_OFFSET = 8

PLAN_NAMES = {
    600: "Starter",
    1500: "Plus",
    4500: "Max",
    30000: "Ultra",
}

# 重置周期识别范围（小时）
HOURLY_RESET_RANGE = (4, 6)
DAILY_RESET_RANGE = (23, 25)


class DataParser:
    """数据解析器"""

    REQUIRED_FIELDS: list[str] = [
        "current_interval_total_count",
        "current_interval_usage_count",
        "start_time",
        "end_time",
        "current_weekly_total_count",
        "current_weekly_usage_count",
        "weekly_start_time",
        "weekly_end_time",
    ]

    def __init__(self, show_year: bool = False, show_first_model_only: bool = False):
        """初始化数据解析器"""
        self._show_year = show_year
        self._show_first_model_only = show_first_model_only

    def format_timestamp(self, ts: int) -> str:
        """将毫秒级时间戳转换为可读字符串"""
        if ts <= 0:
            return "未知"
        dt = datetime.fromtimestamp(
            ts / 1000,
            tz=timezone(timedelta(hours=CHINA_TIMEZONE_OFFSET))
        )
        if self._show_year:
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        return dt.strftime("%m-%d %H:%M:%S")
    
    def _get_plan_name(self, intv_total: int) -> str:
        """根据五小时总额获取套餐名称"""
        return PLAN_NAMES.get(intv_total, "Token Plan")
    
    def _format_duration(self, minutes: int) -> str:
        """格式化时长为"X小时Y分钟"格式"""
        hours = minutes // 60
        mins = minutes % 60
        if hours > 0:
            return f"{hours}小时{mins}分钟"
        return f"{mins}分钟"
    
    def _detect_reset_type(self, start_time: int, end_time: int) -> str:
        """
        识别重置周期类型

        Returns:
            "5h" | "daily" | "unknown"
        """
        if start_time <= 0 or end_time <= 0:
            return "unknown"
        duration_hours = (end_time - start_time) / (1000 * 60 * 60)
        min_hour, max_hour = HOURLY_RESET_RANGE
        if min_hour <= duration_hours <= max_hour:
            return "5h"
        min_hour, max_hour = DAILY_RESET_RANGE
        if min_hour <= duration_hours <= max_hour:
            return "daily"
        return "unknown"

    def parse_quota_data(self, data: Dict[str, Any]) -> str:
        """解析配额数据并格式化输出"""
        base_resp = data.get("base_resp", {})
        status_code = base_resp.get("status_code")

        if status_code is not None and status_code != 0:
            error_msg = base_resp.get("status_msg", "未知错误")
            error_msg_lower = error_msg.lower()
            error_map = {
                "invalid_token": "API Key 无效，请检查配置",
                "token_expired": "API Key 已过期，请重新获取",
                "quota_exceeded": "额度已用尽，请等待重置",
                "rate_limited": "请求过于频繁，请稍后重试",
                "group_not_found": "Group ID 不存在，请检查配置",
                "permission_denied": "无权限访问，请确认账户状态",
            }
            for key, msg in error_map.items():
                if key in error_msg_lower:
                    logger.error(f"API 返回业务错误: {msg} ({error_msg})")
                    raise QueryError(f"API 返回错误：{msg}（{error_msg}）")
            logger.error(f"API 返回未知错误: {error_msg} (状态码: {status_code})")
            raise QueryError(f"API 返回错误：{error_msg}（状态码：{status_code}）")

        model_list = data.get("model_remains", [])
        if not model_list:
            logger.warning("model_remains 列表为空")
            raise QueryError("未获取到任何额度数据，接口返回格式可能已变更")

        logger.info(f"解析额度数据（共 {len(model_list)} 个模型）")

        first_model = model_list[0]
        missing_fields = [f for f in self.REQUIRED_FIELDS if first_model.get(f) is None]
        if missing_fields:
            logger.warning(f"缺少必填字段: {missing_fields}")
            raise QueryError(f"数据格式异常，缺少必填字段: {', '.join(missing_fields)}")

        end_time_ms = first_model.get('end_time', 0)
        if end_time_ms > 0:
            china_tz = timezone(timedelta(hours=CHINA_TIMEZONE_OFFSET))
            end_time = datetime.fromtimestamp(end_time_ms / 1000, tz=china_tz)
            now = datetime.now(tz=china_tz)
            delta = end_time - now
            remains_time_minutes = max(0, int(delta.total_seconds() / 60))
        else:
            remains_time_minutes = 0

        intv_total = first_model.get("current_interval_total_count", 0)
        plan_name = self._get_plan_name(intv_total)

        lines = [f"套餐：MiniMax Token Plan {plan_name}"]

        for idx, model in enumerate(model_list):
            if self._show_first_model_only and idx > 0:
                continue
            
            model_name = model.get("model_name", "未知模型")
            start_time = model.get("start_time", 0)
            end_time = model.get("end_time", 0)
            intv_used = model.get("current_interval_usage_count", 0)
            intv_total = model.get("current_interval_total_count", 0)
            week_used = model.get("current_weekly_usage_count", 0)
            week_total = model.get("current_weekly_total_count", 0)
            
            if intv_total == 0 and week_total == 0 and idx > 0:
                continue
            
            intv_percent = (intv_used / intv_total) * 100 if intv_total > 0 else 0
            week_percent = (week_used / week_total) * 100 if week_total > 0 else 0

            model_reset_type = self._detect_reset_type(start_time, end_time)
            if model_reset_type == "5h":
                intv_label = "5小时使用/总额"
            else:
                intv_label = "日使用/总额"

            lines.append(f"🤖 {model_name}")
            
            if intv_total == 0:
                intv_line = f"{intv_label}：0/0 (0.0%)"
            else:
                intv_line = f"{intv_label}：{intv_used}/{intv_total} ({intv_percent:.1f}%)"
            lines.append(intv_line)
            
            if week_total == 0:
                week_line = "周使用/总额：无周限额"
            else:
                week_line = f"周使用/总额：{week_used}/{week_total} ({week_percent:.1f}%)"
            lines.append(week_line)

        lines.append("")
        
        first_reset_type = self._detect_reset_type(first_model.get('start_time', 0), first_model.get('end_time', 0))
        if first_reset_type == "5h":
            period_name = "5小时滚动周期"
            reset_label = "距离5小时重置"
        elif first_reset_type == "daily":
            period_name = "日周期"
            reset_label = "距离日重置"
        else:
            period_name = "周期"
            reset_label = "距离重置"
        
        lines.append(f"📅 {period_name}：{self.format_timestamp(first_model.get('start_time', 0))} ~ {self.format_timestamp(first_model.get('end_time', 0))}")
        lines.append(f"📅 本周周期：{self.format_timestamp(first_model.get('weekly_start_time', 0))} ~ {self.format_timestamp(first_model.get('weekly_end_time', 0))}")
        lines.append(f"⏰ {reset_label}：{self._format_duration(remains_time_minutes)}")
        lines.append("")
        lines.append("✅ 查询完成！")
        
        return "\n".join(lines)
