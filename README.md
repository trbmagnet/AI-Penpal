# AI-Penpal
AI 笔友是一个基于 Python 的自动邮件回复机器人。它通过 IMAP 协议监控邮箱收件箱，检测新邮件后调用 AI 接口（OpenAI/Anthropic）生成符合预设角色的回复，再通过 SMTP 发送。支持对话记忆和定期摘要。 技术栈：Python 3.11+, CustomTkinter (GUI), SQLite, IMAP/SMTP

2. 运行环境
• 操作系统：Windows 10/11（64位）
• 无需安装 Python，exe 已包含所有依赖
• 需要网络连接（用于 IMAP 收信、SMTP 发信、AI 接口调用）

3. 快速开始
   
3.1 文件准备
将以下文件放在同一个文件夹中：
文件	说明
AI笔友.exe	程序主文件（约28MB）
config.yaml	配置文件（必须）
config.example.yaml	配置参考（可选）

3.2 启动程序
双击 AI笔友.exe 即可启动图形界面。
3.3 首次配置
1. 在 GUI 中切换到「配置编辑」标签页
2. 填写以下必填项：
   • 角色设定：给 AI 取一个名字，设定性格、背景、写作风格
   • AI 模型：选择提供商（openai/anthropic），填入 API 密钥和模型名称
   • 邮箱设置：填入邮箱地址、IMAP/SMTP 服务器、授权码
3. 点击「保存配置」
4. 切换到「运行日志」标签页，点击「启动」开始运行
