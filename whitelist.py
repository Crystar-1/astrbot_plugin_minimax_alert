class WhitelistManager:
    """白名单管理器"""
    
    def __init__(self, whitelist: list[str] = None):
        """初始化白名单管理器"""
        self._whitelist = whitelist.copy() if whitelist else []
    
    def check_whitelist(self, user_sid: str) -> bool:
        """
        检查用户是否在白名单中

        Args:
            user_sid: 用户 session_id

        Returns:
            白名单为空时返回 True（允许所有用户）
        """
        if not self._whitelist:
            return True
        return user_sid in self._whitelist
    
    def add_to_whitelist(self, user_sid: str) -> bool:
        """添加用户到白名单"""
        if user_sid in self._whitelist:
            return False
        self._whitelist.append(user_sid)
        return True
    
    def remove_from_whitelist(self, user_sid: str) -> bool:
        """从白名单移除用户"""
        if user_sid not in self._whitelist:
            return False
        self._whitelist.remove(user_sid)
        return True
    
    def get_whitelist(self) -> list[str]:
        """获取白名单副本"""
        return self._whitelist.copy()
    
    def set_whitelist(self, whitelist: list[str]) -> None:
        """设置白名单"""
        self._whitelist = whitelist.copy() if whitelist else []