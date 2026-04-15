# AstrBot 插件项目

## 项目类型

AstrBot 插件（Python），不是标准Python包。无测试/lint/类型检查配置。

## 核心文件

| 文件 | 作用 |
|------|------|
| `main.py` | 插件入口，`MiniMaxAlertPlugin` 类用 `@register` 装饰 |
| `api.py` | MiniMax API 调用 |
| `parser.py` | 用量数据解析 |
| `config.py` | 配置管理 |
| `whitelist.py` | 白名单管理 |
| `draw.py` | 图片渲染（用 Pillow） |
| `_conf_schema.json` | 插件配置参数定义 |

## 指令

| 指令 | 说明 |
|------|------|
| `/用量` | 查询用量 |
| `/用量 图片` | 以图片模式展示 |

## 依赖

```
aiohttp>=3.9.0
pillow>=10.0.0
httpx>=0.25.0
```

## 构建/安装

将整个目录复制到 AstrBot 的 `data/plugins/` 目录。

## 注意事项

1. API Key 通过插件配置页面配置，非环境变量
2. 白名单基于 `session_id`，非用户ID
3. 国际版需要额外配置 `group_id`