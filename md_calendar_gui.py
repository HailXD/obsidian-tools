import calendar
from datetime import date
import os
import tkinter as tk
from collections import defaultdict
from tkinter import ttk

from md_calendar_data import load_entries

APP_TITLE = "Markdown Calendar"
DAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
SORTS = ("date", "tasks", "notes")
EMPTY_DAY = ""
PREVIEW_LIMIT = 120
CELL_WIDTH = 12
CELL_HEIGHT = 4
PAD = 6


class App:
    def __init__(self, root):
        self.root = root
        self.entries = load_entries()
        self.entry_by_name = {entry.name: entry for entry in self.entries}
        self.entries_by_day = defaultdict(list)
        for entry in self.entries:
            self.entries_by_day[entry.day].append(entry)
        self.months = sorted({(entry.day.year, entry.day.month) for entry in self.entries})
        self.month_index = len(self.months) - 1 if self.months else 0
        self.sort_var = tk.StringVar(value=SORTS[0])
        self.status_var = tk.StringVar()
        self.calendar_buttons = []
        self.tree_ids = {}
        self.selected_name = None

        self.root.title(APP_TITLE)
        self.root.geometry("1200x760")
        self.build()
        self.refresh()

    def build(self):
        top = ttk.Frame(self.root, padding=PAD)
        top.pack(fill="x")
        ttk.Button(top, text="<", width=3, command=self.show_prev_month).pack(side="left")
        self.month_label = ttk.Label(top, width=18, anchor="center")
        self.month_label.pack(side="left", padx=PAD)
        ttk.Button(top, text=">", width=3, command=self.show_next_month).pack(side="left")
        ttk.Label(top, text="Sort").pack(side="left", padx=(PAD * 2, PAD))
        sort_box = ttk.Combobox(top, textvariable=self.sort_var, values=SORTS, width=8, state="readonly")
        sort_box.pack(side="left")
        sort_box.bind("<<ComboboxSelected>>", lambda _: self.refresh_list())
        ttk.Label(top, textvariable=self.status_var).pack(side="right")

        body = ttk.Panedwindow(self.root, orient="horizontal")
        body.pack(fill="both", expand=True, padx=PAD, pady=(0, PAD))

        left = ttk.Frame(body, padding=PAD)
        right = ttk.Frame(body, padding=PAD)
        body.add(left, weight=3)
        body.add(right, weight=4)

        self.build_calendar(left)
        self.build_list(right)
        self.build_preview(right)

    def build_calendar(self, parent):
        frame = ttk.LabelFrame(parent, text="Calendar", padding=PAD)
        frame.pack(fill="both", expand=True)
        for column, name in enumerate(DAY_NAMES):
            ttk.Label(frame, text=name, anchor="center").grid(row=0, column=column, sticky="ew", padx=2, pady=2)
            frame.grid_columnconfigure(column, weight=1)
        for row in range(6):
            frame.grid_rowconfigure(row + 1, weight=1)
            row_buttons = []
            for column in range(7):
                button = tk.Button(
                    frame,
                    width=CELL_WIDTH,
                    height=CELL_HEIGHT,
                    anchor="nw",
                    justify="left",
                    command=lambda day=None: self.select_day(day),
                )
                button.grid(row=row + 1, column=column, sticky="nsew", padx=2, pady=2)
                row_buttons.append(button)
            self.calendar_buttons.append(row_buttons)

    def build_list(self, parent):
        frame = ttk.LabelFrame(parent, text="Entries", padding=PAD)
        frame.pack(fill="both", expand=True)
        columns = ("date", "tasks", "notes")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=12)
        self.tree.heading("date", text="Date", command=lambda: self.set_sort("date"))
        self.tree.heading("tasks", text="Tasks", command=lambda: self.set_sort("tasks"))
        self.tree.heading("notes", text="Notes", command=lambda: self.set_sort("notes"))
        self.tree.column("date", width=120, anchor="w")
        self.tree.column("tasks", width=70, anchor="center")
        self.tree.column("notes", width=80, anchor="center")
        self.tree.pack(fill="both", expand=True, side="left")
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<Double-1>", lambda _: self.open_selected())
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(fill="y", side="right")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def build_preview(self, parent):
        frame = ttk.LabelFrame(parent, text="Preview", padding=PAD)
        frame.pack(fill="both", expand=True, pady=(PAD, 0))
        info = ttk.Frame(frame)
        info.pack(fill="x")
        self.title_label = ttk.Label(info)
        self.title_label.pack(side="left")
        ttk.Button(info, text="Open Markdown", command=self.open_selected).pack(side="right")
        self.preview = tk.Text(frame, wrap="word", height=18)
        self.preview.pack(fill="both", expand=True, pady=(PAD, 0))
        self.preview.configure(state="disabled")

    def show_prev_month(self):
        if self.months and self.month_index > 0:
            self.month_index -= 1
            self.refresh_calendar()

    def show_next_month(self):
        if self.months and self.month_index < len(self.months) - 1:
            self.month_index += 1
            self.refresh_calendar()

    def set_sort(self, value):
        self.sort_var.set(value)
        self.refresh_list()

    def refresh(self):
        self.refresh_calendar()
        self.refresh_list()
        if self.entries:
            self.show_entry(self.entries[-1].name)

    def refresh_calendar(self):
        if not self.months:
            self.month_label.config(text="No markdown files")
            return
        year, month = self.months[self.month_index]
        self.month_label.config(text=f"{calendar.month_name[month]} {year}")
        month_days = calendar.Calendar(firstweekday=0).monthdayscalendar(year, month)
        while len(month_days) < 6:
            month_days.append([0] * 7)
        for row, week in enumerate(month_days):
            for column, day_num in enumerate(week):
                self.update_day_button(self.calendar_buttons[row][column], year, month, day_num)
        count = sum(1 for entry in self.entries if entry.day.year == year and entry.day.month == month)
        self.status_var.set(f"{count} files")

    def update_day_button(self, button, year, month, day_num):
        if not day_num:
            button.config(text=EMPTY_DAY, state="disabled", relief="flat", bg="#f0f0f0")
            return
        day = date(year, month, day_num)
        items = self.entries_by_day.get(day, [])
        if not items:
            button.config(text=str(day_num), state="disabled", relief="flat", bg="#f4f4f4")
            return
        primary = sorted(items, key=lambda entry: entry.name)[0]
        preview = primary.notes_text[:PREVIEW_LIMIT].replace("\n", " ")
        text = f"{day_num}\nF {len(items)}  T {sum(entry.task_count for entry in items)}\n{preview}"
        active = any(entry.name == self.selected_name for entry in items)
        button.config(
            text=text,
            state="normal",
            relief="sunken" if active else "raised",
            bg="#dbeafe" if active else "#ffffff",
            command=lambda value=day: self.select_day(value),
        )

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree_ids.clear()
        for entry in self.sorted_entries():
            item = self.tree.insert(
                "",
                "end",
                iid=entry.name,
                values=(entry.day.isoformat(), entry.task_count, entry.notes_length),
            )
            self.tree_ids[entry.name] = item
        if self.selected_name in self.tree_ids:
            self.tree.selection_set(self.tree_ids[self.selected_name])

    def sorted_entries(self):
        sort_name = self.sort_var.get()
        if sort_name == "tasks":
            return sorted(self.entries, key=lambda entry: (-entry.task_count, -entry.notes_length, entry.day))
        if sort_name == "notes":
            return sorted(self.entries, key=lambda entry: (-entry.notes_length, -entry.task_count, entry.day))
        return sorted(self.entries, key=lambda entry: entry.day)

    def select_day(self, day):
        items = self.entries_by_day.get(day, [])
        if items:
            self.show_entry(sorted(items, key=lambda entry: entry.name)[0].name)

    def on_tree_select(self, _):
        current = self.tree.selection()
        if not current:
            return
        self.show_entry(current[0])

    def show_entry(self, name):
        entry = self.entry_by_name.get(name)
        if not entry:
            return
        self.selected_name = name
        self.title_label.config(text=f"{entry.name} | Tasks {entry.task_count} | Notes {entry.notes_length}")
        self.preview.configure(state="normal")
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", entry.content)
        self.preview.configure(state="disabled")
        if name in self.tree_ids:
            self.tree.selection_set(self.tree_ids[name])
            self.tree.see(self.tree_ids[name])
        self.refresh_calendar()

    def open_selected(self):
        if self.selected_name:
            os.startfile(self.entry_by_name[self.selected_name].path)


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
