import customtkinter as ctk


def create_labeled_entry(parent, label_text: str, default_value: str = "",
                         show: str = None, width: int = 300) -> ctk.CTkEntry:
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="x", padx=10, pady=4)
    ctk.CTkLabel(frame, text=label_text, width=140, anchor="w").pack(side="left")
    entry = ctk.CTkEntry(frame, width=width, show=show)
    entry.insert(0, default_value)
    entry.pack(side="left", padx=(10, 0), fill="x", expand=True)
    return entry


def create_labeled_textbox(parent, label_text: str, default_value: str = "",
                           height: int = 80, width: int = 300) -> ctk.CTkTextbox:
    ctk.CTkLabel(parent, text=label_text, anchor="w").pack(fill="x", padx=10, pady=(8, 2))
    textbox = ctk.CTkTextbox(parent, height=height, width=width)
    textbox.pack(padx=10, fill="x")
    if default_value:
        textbox.insert("1.0", default_value)
    return textbox


def create_labeled_switch(parent, label_text: str, default_value: bool = False) -> ctk.CTkSwitch:
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="x", padx=10, pady=4)
    ctk.CTkLabel(frame, text=label_text, width=140, anchor="w").pack(side="left")
    switch = ctk.CTkSwitch(frame, text="")
    if default_value:
        switch.select()
    switch.pack(side="left", padx=(10, 0))
    return switch


def create_labeled_optionmenu(parent, label_text: str, values: list[str],
                              default: str = None) -> ctk.CTkOptionMenu:
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="x", padx=10, pady=4)
    ctk.CTkLabel(frame, text=label_text, width=140, anchor="w").pack(side="left")
    var = ctk.StringVar(value=default or values[0])
    menu = ctk.CTkOptionMenu(frame, variable=var, values=values)
    menu.pack(side="left", padx=(10, 0))
    return menu
