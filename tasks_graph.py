import os
import re
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, date, timedelta

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")
TASK_PATTERN = re.compile(r"^-\s*\[[ xX]?\]", re.MULTILINE)
TARGET_COUNT = 3
FIG_SIZE = (14, 7)
ZOOM_SCALE = 1.2
PAN_SCALE = 1 / 3
ZERO_COLOR = "#888888"
Y_PADDING = 0.25


def get_date_files():
    """
    Return a sorted list of files in the current directory that match the YYYY-MM-DD.md pattern.
    """
    date_files = []
    for filename in os.listdir("."):
        if not DATE_PATTERN.match(filename):
            continue
        try:
            datetime.strptime(filename, "%Y-%m-%d.md")
            date_files.append(filename)
        except ValueError:
            print(f"Warning: Skipping invalid date filename: {filename}")
    return sorted(date_files)


def get_task_count(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return len(TASK_PATTERN.findall(file.read()))


def build_series(date_files):
    counts_by_date = {}
    for filename in date_files:
        current_date = date.fromisoformat(filename.split(".md")[0])
        counts_by_date[current_date] = get_task_count(filename)
    if not counts_by_date:
        return [], []
    dates = []
    counts = []
    current_date = min(counts_by_date)
    end_date = max(counts_by_date)
    while current_date <= end_date:
        dates.append(current_date)
        counts.append(counts_by_date.get(current_date, 0))
        current_date += timedelta(days=1)
    return dates, counts


def get_zero_marker_dates(dates, counts):
    zero_dates = []
    start_index = None
    for index, count in enumerate(counts):
        if count == 0:
            if start_index is None:
                start_index = index
            continue
        if start_index is None:
            continue
        zero_dates.append(dates[start_index])
        if start_index != index - 1:
            zero_dates.append(dates[index - 1])
        start_index = None
    if start_index is not None:
        zero_dates.append(dates[start_index])
        if start_index != len(dates) - 1:
            zero_dates.append(dates[-1])
    return zero_dates


def connect_interactions(fig, ax, line, dates, counts):
    state = {"x": None, "limits": None}
    annotation = ax.annotate(
        "",
        xy=(0, 0),
        xytext=(10, 10),
        textcoords="offset points",
        bbox={"boxstyle": "round,pad=0.25", "fc": "black", "ec": "#666666", "alpha": 0.9},
    )
    annotation.set_visible(False)

    def on_scroll(event):
        if event.inaxes != ax or event.xdata is None:
            return
        scale = 1 / ZOOM_SCALE if event.button == "up" else ZOOM_SCALE
        left, right = ax.get_xlim()
        width = right - left
        if width <= 0:
            return
        x_ratio = (event.xdata - left) / (right - left)
        new_width = max(width * scale, 1)
        ax.set_xlim(event.xdata - new_width * x_ratio, event.xdata + new_width * (1 - x_ratio))
        fig.canvas.draw_idle()

    def on_press(event):
        if event.inaxes != ax or event.button != 1 or event.x is None:
            return
        state["x"] = event.x
        state["limits"] = ax.get_xlim()
        if annotation.get_visible():
            annotation.set_visible(False)
            fig.canvas.draw_idle()

    def on_release(event):
        state["x"] = None
        state["limits"] = None

    def on_motion(event):
        if state["x"] is None or state["limits"] is None or event.inaxes != ax or event.x is None:
            if annotation.get_visible():
                annotation.set_visible(False)
                fig.canvas.draw_idle()
            return
        axis_width = ax.bbox.width
        if axis_width <= 0:
            return
        left, right = state["limits"]
        delta = (state["x"] - event.x) * (right - left) / axis_width
        ax.set_xlim(left + delta, right + delta)
        fig.canvas.draw_idle()

    def on_hover(event):
        if state["x"] is not None:
            return
        if event.inaxes != ax:
            if annotation.get_visible():
                annotation.set_visible(False)
                fig.canvas.draw_idle()
            return
        contains, info = line.contains(event)
        indices = info.get("ind", [])
        if not contains or len(indices) == 0:
            if annotation.get_visible():
                annotation.set_visible(False)
                fig.canvas.draw_idle()
            return
        index = indices[0]
        annotation.xy = (dates[index], counts[index])
        annotation.set_text(f"{dates[index]:%Y-%m-%d}")
        annotation.set_visible(True)
        fig.canvas.draw_idle()

    def on_key(event):
        if event.key not in {"left", "right"}:
            return
        left, right = ax.get_xlim()
        width = right - left
        if width <= 0:
            return
        delta = width * PAN_SCALE
        if event.key == "left":
            ax.set_xlim(left - delta, right - delta)
        else:
            ax.set_xlim(left + delta, right + delta)
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("scroll_event", on_scroll)
    fig.canvas.mpl_connect("button_press_event", on_press)
    fig.canvas.mpl_connect("button_release_event", on_release)
    fig.canvas.mpl_connect("motion_notify_event", on_motion)
    fig.canvas.mpl_connect("motion_notify_event", on_hover)
    fig.canvas.mpl_connect("key_press_event", on_key)


def main():
    try:
        plt.style.use("dark_background")
    except OSError:
        print("Warning: 'dark_background' style not found. Using default.")

    date_files = get_date_files()

    print(f"Found {len(date_files)} date files.")

    dates, counts = build_series(date_files)

    if not dates:
        print("No data to plot.")
        return

    fig, ax = plt.subplots(figsize=FIG_SIZE)
    line, = ax.plot(dates, counts, linewidth=2, label="Tasks")
    line.set_pickradius(8)
    connect_interactions(fig, ax, line, dates, counts)
    non_zero_dates = [current_date for current_date, count in zip(dates, counts) if count != 0]
    non_zero_counts = [count for count in counts if count != 0]
    if non_zero_dates:
        ax.scatter(non_zero_dates, non_zero_counts, s=18, color=line.get_color(), zorder=4)
    zero_dates = get_zero_marker_dates(dates, counts)
    if zero_dates:
        ax.scatter(zero_dates, [0] * len(zero_dates), s=18, facecolors="none", edgecolors=ZERO_COLOR, linewidths=0.9, alpha=0.8, zorder=4)
    ax.axhline(y=TARGET_COUNT, color="red", linestyle="--", label=f"Target ({TARGET_COUNT})")
    ax.axhline(y=0, color=ZERO_COLOR, linestyle=":", linewidth=0.8, alpha=0.35)

    today = date.today()
    if dates[0] <= today <= dates[-1]:
        ax.axvline(x=today, color="lime", linestyle=":", linewidth=2, label=f"Today ({today:%Y-%m-%d})")

    locator = mdates.AutoDateLocator(minticks=5, maxticks=20)
    formatter = mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)

    ax.set_title("Number of Tasks per Day")
    ax.set_xlabel("Date")
    ax.set_ylabel("Task Count")
    ax.set_ylim(bottom=-Y_PADDING)
    ax.set_xlim(dates[0] - timedelta(days=1), dates[-1] + timedelta(days=1))
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend()

    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
