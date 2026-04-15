class WhitelistManager:
    """白名单管理器"""
    
    def __init__(self, whitelist: list[str] = None):
        """初始化白名单管理器"""
        self._whitelist = whitelist.copy() if whitelist else []
    
    def check_whitelist(self, user_sid: str) -> bool:
        """
        检查用户是否在白名单中
        Returns:
            白名单为空时返回 True（允许所有用户）
        """
        if not self._whitelist:
            return True
        return user_sid in self._whitelist
    
    def get_whitelist(self) -> list[str]:
        """获取白名单副本"""
        return self._whitelist.copy()