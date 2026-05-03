import customtkinter as ctk

from tracker import ReplyTracker


class HistoryViewerTab(ctk.CTkFrame):
    def __init__(self, parent, db_path: str):
        super().__init__(parent, fg_color="transparent")
        self.db_path = db_path
        self.tracker: ReplyTracker | None = None
        self._build_ui()
        self._refresh_senders()

    def _open_tracker(self):
        if self.tracker is None:
            self.tracker = ReplyTracker(self.db_path)

    def _build_ui(self):
        left = ctk.CTkFrame(self, width=250)
        left.pack(side="left", fill="y", padx=(5, 0), pady=5)

        ctk.CTkLabel(left, text="联系人", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)

        self.sender_list = ctk.CTkScrollableFrame(left)
        self.sender_list.pack(fill="both", expand=True, padx=5, pady=5)

        ctk.CTkButton(left, text="刷新", command=self._refresh_senders).pack(pady=5)

        right = ctk.CTkFrame(self)
        right.pack(side="right", fill="both", expand=True, padx=(5, 5), pady=5)

        self.conversation_text = ctk.CTkTextbox(
            right, state="disabled", wrap="word",
            font=ctk.CTkFont(size=13),
        )
        self.conversation_text.pack(fill="both", expand=True, padx=5, pady=5)

    def _refresh_senders(self):
        self._open_tracker()
        for widget in self.sender_list.winfo_children():
            widget.destroy()

        try:
            cursor = self.tracker._conn.execute(
                "SELECT DISTINCT sender FROM conversation_history ORDER BY sender"
            )
            senders = [row[0] for row in cursor.fetchall()]
        except Exception:
            senders = []

        for sender in senders:
            btn = ctk.CTkButton(
                self.sender_list, text=sender, anchor="w",
                command=lambda s=sender: self._show_conversation(s),
            )
            btn.pack(fill="x", padx=2, pady=2)

        if not senders:
            ctk.CTkLabel(self.sender_list, text="暂无对话记录",
                         text_color="gray").pack(pady=10)

    def _show_conversation(self, sender: str):
        self._open_tracker()
        history = self.tracker.get_history(sender, limit=100)

        self.conversation_text.configure(state="normal")
        self.conversation_text.delete("1.0", "end")

        summary = self.tracker.get_summary(sender)
        if summary:
            self.conversation_text.insert("end", "=== 对话摘要 ===\n")
            self.conversation_text.insert("end", summary["summary_text"] + "\n\n")

        self.conversation_text.insert("end", f"=== 与 {sender} 的对话 ===\n\n")

        for msg in history:
            role_label = "[用户]" if msg["role"] == "user" else "[AI助手]"
            timestamp = msg["timestamp"][:19] if msg["timestamp"] else ""
            subject = f" | 主题: {msg['subject']}" if msg.get("subject") else ""
            self.conversation_text.insert("end", f"{role_label} {timestamp}{subject}\n")
            self.conversation_text.insert("end", f"{msg['content']}\n\n")

        self.conversation_text.configure(state="disabled")

    def refresh(self):
        self._refresh_senders()

    def close(self):
        if self.tracker:
            self.tracker.close()
