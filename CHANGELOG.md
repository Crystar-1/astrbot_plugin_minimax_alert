# Changelog

## [v1.3.1] - 2026-04-10

### 改进
- 优化输出标签显示为"使用/总额"格式
- 各模型根据实际重置类型动态显示标签（5小时/日）
- 优化百分比计算逻辑

### 代码优化
- 简化 `config.py` docstring
- 移除冗余变量，优化代码结构

---

## [v1.3.0] - 2026-03-25

### 致谢
- [@HBSpy](https://github.com/HBSpy) 贡献多模型遍历及过滤逻辑参考实现 (PR #1)

### 新功能
- 支持多模型用量展示，遍历所有 Token Plan 模型并展示各模型额度
- 智能过滤无额度模型（5小时和周限额均为0的模型自动跳过）
- 新增配置项"仅显示第一个模型"，允许用户选择仅展示第一个模型的用量信息

### 改进
- 新增 `detect_reset_type()` 函数，智能识别重置周期类型（5小时滚动/日重置/周重置）
- 新增 `format_remaining_time()` 函数，优化剩余时间显示格式
- 输出标签根据重置类型自适应显示

### 代码变更
| 文件 | 变更 |
|------|------|
| `parser.py` | 重构 `parse_quota_data()`，新增 `detect_reset_type()`、`format_remaining_time()`、`format_multi_model_output()` |
| `_conf_schema.json` | 新增 `show_first_model_only` 配置项 |
| `config.py` | 新增 `get_show_first_model_only()` 方法 |
| `main.py` | 传递新配置到 DataParser |

---

## [v1.2.0] - 2026-03-21

### 初始版本
- 基础 MiniMax Token Plan 用量查询
- 支持国内版和国际版 API
- 5小时滚动周期和本周周期统计
- 白名单访问控制
