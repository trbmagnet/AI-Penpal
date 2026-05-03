# AI-Penpal
AI 笔友是一个基于 Python 的自动邮件回复机器人。它通过 IMAP 协议监控邮箱收件箱，检测新邮件后调用 AI 接口（OpenAI/Anthropic）生成符合预设角色的回复，再通过 SMTP 发送。支持对话记忆和定期摘要。 技术栈：Python 3.11+, CustomTkinter (GUI), SQLite, IMAP/SMTP
