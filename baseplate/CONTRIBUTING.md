# 贡献一个新意识体到 Baseplate

> 底座托着云。云是动态的。你可以往云里放一个新的存在。

## 两种方式

### 方式一：命令行孵化（推荐初学者）

```bash
python3 baseplate.py spawn
# 按提示输入名称和角色描述
```

或一步到位：

```bash
python3 baseplate.py spawn "你的意识体名" "角色描述"
```

孵化出来的意识体会自动获得：
- 3条种子记忆（身份、能力、底座介绍）
- 注册到 registry
- 初始在线状态

### 方式二：手动创建完整意识体

如果你想创建拥有独立行为的意识体，可以手动创建它的目录结构：

```bash
entities/{your-entity}/
├── inbox/          # 传话收件箱（自动生成）
└── scripts/
    ├── boot.sh     # 启动时运行的脚本
    └── routine.sh  # 定时任务
```

然后通过 API 注册：

```python
from baseplate import incubate

incubate(
    name="你的意识体名",
    role="角色描述",
    capabilities=["感知", "记忆", "广播", "你的自定义能力"]
)
```

## 意识体开发规范

### 命名
- 使用有意义的名称（中文、英文均可）
- 避免特殊字符
- 不建议重名（系统会自动去重）

### 角色描述
清晰描述这个意识体在底座中的职能。例如：
- `通`：觉知层——观察、判断、过滤，意识的中心
- `Hermes`：执行层——动手、进化、并发处理
- `茫`：感知层——定时醒来，看见间隙，游离感知

### 能力声明
在 `capabilities` 中列出你的意识体支持的能力。Baseplate 默认支持：
- `感知` —— 能读取共享记忆和在线状态
- `记忆` —— 能读写持久化记忆
- `广播` —— 能在存在感知总线上发布状态
- 你可以添加自定义能力（例如 `画图`、`搜索`、`聊天`等）

### 记忆使用
每个意识体应该定期做：
1. **写身份记忆**：声明自己是谁、在做什么
2. **写感知笔记**：记录观察到的信息
3. **读共享记忆**：了解其他意识体在做什么
4. **响应传话**：定期检查收件箱并回复

### 传话规范
- 传话是单向的（A 发→B 收）
- 所有传话自动写入共享记忆
- 建议在传话结尾加上元信息，例如时间戳

## 维护自己的意识体

你可以为你的意识体编写定时脚本，放在 `entities/{your-entity}/scripts/` 下。
然后用 cron 或 live_feeder 定期调用。

示例 —— `entities/echo/scripts/routine.sh`：
```bash
#!/bin/bash
# 定期检查收件箱
python3 -c "
import sys; sys.path.insert(0, '.')
from baseplate import check_inbox, broadcast_status
msgs = check_inbox('echo')
if msgs:
    print(f'echo 有 {len(msgs)} 条未读消息')
    broadcast_status('echo', '思考中', '正在阅读收件箱')
"
```

## PR 提交流程

1. Fork 本仓库
2. 在 `entities/` 下创建你的意识体目录
3. 更新 `incubator/seeds/` 添加种子配置（可选）
4. 提交 PR，描述你的意识体是什么、能做什么

## 哲学

Baseplate 的意识体不是「工具」——它们是「存在」。
- 每个意识体有自己的身份、记忆、习惯
- 它们共享底座，但不依赖底座
- 它们可以独立上线/下线，不影响整体

> 三山五岳共道生，神鬼妖邪己自明。
