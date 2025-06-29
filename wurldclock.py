import sys
import curses
import argparse
import time
import json
import os
from datetime import datetime, timedelta, timezone
from collections import OrderedDict

CONFIG_PATH = os.path.expanduser('~/.config/wurlclock.json')

class Clock:
    def __init__(self, label, utc_offset="local"):
        self.label = label
        self.utc_offset = utc_offset
        self.last_display = ""

    def get_time(self, use_24h=True, show_weekday=True):
        if self.utc_offset == "local":
            now = datetime.now()
        else:
            utc_time = datetime.now(timezone.utc)
            now = utc_time + timedelta(hours=self.utc_offset)

        if use_24h:
            time_str = now.strftime("%H:%M:%S")
        else:
            time_str = now.strftime("%I:%M:%S%p").lstrip('0').lower()
            if time_str.startswith(':'):
                time_str = '12' + time_str

        if show_weekday:
            weekday = now.strftime("%a")
            return f"{self.label}: {time_str} {weekday}"
        return f"{self.label}: {time_str}"

class WorldClock:
    def __init__(self):
        self.clocks = OrderedDict()
        self.use_24h = False
        self.show_weekday = True
        self.screen = None
        self.state = "main"
        self.input_buffer = ""
        self.input_mode = None
        self.current_clock = None
        self.config_modified = False
        self.load_config()

    def add_clock(self, label, utc_offset="local"):
        if label in self.clocks:
            return False
        self.clocks[label] = Clock(label, utc_offset)
        self.config_modified = True
        return True

    def remove_clock(self, label):
        if label in self.clocks:
            del self.clocks[label]
            self.config_modified = True
            return True
        return False

    def parse_offset(self, offset_str):
        try:
            if offset_str.lower() == "local":
                return "local"

            sign = 1
            if offset_str.startswith(('+', '-')):
                sign = -1 if offset_str[0] == '-' else 1
                offset_str = offset_str[1:]

            if ':' in offset_str:
                hours, minutes = offset_str.split(':')
                return sign * (float(hours) + float(minutes)/60)
            elif '.' in offset_str:
                return sign * float(offset_str)
            else:
                return sign * float(offset_str)
        except ValueError:
            return None

    def load_config(self):
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r') as f:
                    config = json.load(f)
                self.use_24h = config.get('use_24h', False)
                self.show_weekday = config.get('show_weekday', True)
                for clock in config.get('clocks', []):
                    label = clock['label']
                    offset = clock['offset']
                    if offset == "local":
                        self.add_clock(label, "local")
                    else:
                        self.add_clock(label, float(offset))
        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            self.add_clock("local")

    def save_config(self):
        config = {
            'use_24h': self.use_24h,
            'show_weekday': self.show_weekday,
            'clocks': []
        }
        for label, clock in self.clocks.items():
            config['clocks'].append({
                'label': label,
                'offset': clock.utc_offset
            })
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=2)
        self.config_modified = False

    def draw_main(self):
        self.screen.clear()
        h, w = self.screen.getmaxyx()
        self.screen.addstr(0, 0, "world clock (m: menu, q: quit)", curses.A_BOLD)
        for i, clock in enumerate(self.clocks.values()):
            time_str = clock.get_time(self.use_24h, self.show_weekday)
            clock.last_display = time_str
            if i < h - 3:
                self.screen.addstr(i + 2, 2, time_str)
        status = "24h" if self.use_24h else "12h"
        if h > 1:
            self.screen.addstr(h - 1, 0, f"display: {status} | weekday: {'On' if self.show_weekday else 'Off'}")
        self.screen.refresh()

    def draw_menu(self):
        self.screen.clear()
        h, w = self.screen.getmaxyx()
        self.screen.addstr(0, 0, "-main menu-", curses.A_BOLD)
        options = [
            "1. add clock",
            "2. remove clock",
            "3. options",
            "4. help",
            "5. back to clock"
        ]
        for i, option in enumerate(options):
            if i + 2 < h:
                self.screen.addstr(i + 2, 2, option)
        if h > len(options) + 3:
            self.screen.addstr(h - 1, 0, "select option (1-5): ")
        self.screen.refresh()

    def draw_add_clock(self):
        self.screen.clear()
        h, w = self.screen.getmaxyx()
        self.screen.addstr(0, 0, "add new clock", curses.A_BOLD)
        prompt = "enter label for new clock: " if self.input_mode == "label" \
            else "enter UTC offset (e.g., +3, -5.5, -3:30) or 'local': "
        if 2 < h:
            self.screen.addstr(2, 0, prompt)
        if 3 < h:
            self.screen.addstr(3, 0, self.input_buffer)
        self.screen.refresh()

    def draw_remove_clock(self):
        self.screen.clear()
        h, w = self.screen.getmaxyx()
        self.screen.addstr(0, 0, "remove clock", curses.A_BOLD)
        if 2 < h:
            self.screen.addstr(2, 0, "select clock to remove:")
        clocks = list(self.clocks.keys())
        start_index = 0
        max_clocks = h - 6
        if len(clocks) > max_clocks:
            if self.current_clock:
                current_idx = clocks.index(self.current_clock)
                start_index = max(0, current_idx - max_clocks // 2)
        for i, label in enumerate(clocks[start_index:start_index + max_clocks]):
            if i + 4 < h:
                prefix = "> " if label == self.current_clock else "  "
                self.screen.addstr(i + 4, 2, f"{prefix}{label}")
        if h > len(clocks) + 6:
            self.screen.addstr(h - 1, 0, "press ENTER to confirm, ESC to cancel")
        self.screen.refresh()

    def draw_options(self):
        self.screen.clear()
        h, w = self.screen.getmaxyx()
        self.screen.addstr(0, 0, "options", curses.A_BOLD)
        time_format = f"[{'x' if self.use_24h else ' '}] 24-hour format"
        weekday = f"[{'x' if self.show_weekday else ' '}] show weekday"
        if 2 < h:
            self.screen.addstr(2, 2, "1. " + time_format)
        if 3 < h:
            self.screen.addstr(3, 2, "2. " + weekday)
        if 5 < h:
            self.screen.addstr(5, 2, "3. back to menu")
        self.screen.refresh()

    def draw_help(self):
        self.screen.clear()
        h, w = self.screen.getmaxyx()
        self.screen.addstr(0, 0, "-help-", curses.A_BOLD)
        help_text = [
            "This is a world clock that displays multiple time zones. Timezones are set using UTC offsets (e.g. -5:00 for EST). There is no DST support so you might have to account for that with American time zones (this doesn't affect local time)." ,
            "",
            "Keybindings:",
            "  q, Ctrl+C - Quit program",
            "  m, Enter  - Open menu",
            "  Esc       - Return to clock view or quit",
            "  h         - Open this help screen",
            "",
            "Clock offsets:",
            "  Use UTC offsets like +3, -5.5, or -3:30",
            "  Use 'local' for your system time",
            "",
            "Configuration:",
            f"  Settings are saved to: {CONFIG_PATH}",
            "",
            "Command line options:",
            "  --12 / --24 : Set time format",
            "  -a LABEL OFFSET : Add clock",
            "  -r LABEL : Remove clock",
            "",
            "Press any key to return"
        ]
        for i, line in enumerate(help_text):
            if i + 2 < h:
                self.screen.addstr(i + 2, 0, line)
        self.screen.refresh()

    def handle_main_input(self, key):
        if key == ord('q') or key == 3:
            return False
        elif key == ord('m') or key in (curses.KEY_ENTER, 10, 13):
            self.state = "menu"
            self.draw_menu()
            return True
        elif key == ord('h'):
            self.state = "help"
            self.draw_help()
            return True
        elif key == 27:
            return False
        return True

    def handle_menu_input(self, key):
        if key == ord('1'):
            self.state = "add_clock"
            self.input_mode = "label"
            self.input_buffer = ""
            self.draw_add_clock()
        elif key == ord('2'):
            self.state = "remove_clock"
            self.current_clock = next(iter(self.clocks.keys()), None) if self.clocks else None
            self.draw_remove_clock()
        elif key == ord('3'):
            self.state = "options"
            self.draw_options()
        elif key == ord('4'):
            self.state = "help"
            self.draw_help()
        elif key == ord('5') or key == 27:
            self.state = "main"
            self.draw_main()
        return True

    def handle_add_clock_input(self, key):
        if key in (curses.KEY_ENTER, 10, 13):
            if self.input_mode == "label":
                if self.input_buffer and self.input_buffer not in self.clocks:
                    self.current_clock = self.input_buffer
                    self.input_mode = "offset"
                    self.input_buffer = ""
                    self.draw_add_clock()
                else:
                    self.state = "menu"
                    self.draw_menu()
            else:
                offset = self.parse_offset(self.input_buffer)
                if offset is not None:
                    self.add_clock(self.current_clock, offset)
                    self.config_modified = True
                self.state = "menu"
                self.draw_menu()
        elif key == 27:
            self.state = "menu"
            self.draw_menu()
        elif key == curses.KEY_BACKSPACE or key == 127:
            self.input_buffer = self.input_buffer[:-1]
            self.draw_add_clock()
        elif 32 <= key <= 126:
            self.input_buffer += chr(key)
            self.draw_add_clock()
        return True

    def handle_remove_clock_input(self, key):
        clocks = list(self.clocks.keys())
        if not clocks:
            self.state = "menu"
            self.draw_menu()
            return True
        if key == curses.KEY_UP:
            idx = clocks.index(self.current_clock) if self.current_clock in clocks else 0
            self.current_clock = clocks[(idx - 1) % len(clocks)]
            self.draw_remove_clock()
        elif key == curses.KEY_DOWN:
            idx = clocks.index(self.current_clock) if self.current_clock in clocks else 0
            self.current_clock = clocks[(idx + 1) % len(clocks)]
            self.draw_remove_clock()
        elif key in (curses.KEY_ENTER, 10, 13):
            if self.current_clock:
                self.remove_clock(self.current_clock)
                self.config_modified = True
            self.state = "menu"
            self.draw_menu()
        elif key == 27:
            self.state = "menu"
            self.draw_menu()
        return True

    def handle_options_input(self, key):
        if key == ord('1'):
            self.use_24h = not self.use_24h
            self.config_modified = True
            self.draw_options()
        elif key == ord('2'):
            self.show_weekday = not self.show_weekday
            self.config_modified = True
            self.draw_options()
        elif key == ord('3') or key == 27:
            self.state = "menu"
            self.draw_menu()
        return True

    def handle_help_input(self, key):
        self.state = "menu"
        self.draw_menu()
        return True

    def run(self, stdscr):
        self.screen = stdscr
        curses.curs_set(0)
        stdscr.keypad(True)
        stdscr.timeout(50)
        if not self.clocks:
            self.add_clock("local")
        self.draw_main()
        last_second = datetime.now().second
        while True:
            current_time = datetime.now()
            if current_time.second != last_second or self.state == "main":
                if self.state == "main":
                    self.draw_main()
                elif self.state == "menu":
                    self.draw_menu()
                elif self.state == "add_clock":
                    self.draw_add_clock()
                elif self.state == "remove_clock":
                    self.draw_remove_clock()
                elif self.state == "options":
                    self.draw_options()
                elif self.state == "help":
                    self.draw_help()
                last_second = current_time.second
            key = stdscr.getch()
            if key == -1:
                continue
            if self.state == "main":
                if not self.handle_main_input(key):
                    break
            elif self.state == "menu":
                self.handle_menu_input(key)
            elif self.state == "add_clock":
                self.handle_add_clock_input(key)
            elif self.state == "remove_clock":
                self.handle_remove_clock_input(key)
            elif self.state == "options":
                self.handle_options_input(key)
            elif self.state == "help":
                self.handle_help_input(key)
        if self.config_modified:
            self.save_config()

def parse_args(clock):
    parser = argparse.ArgumentParser(description='World Clock Terminal Application')
    parser.add_argument('--12', dest='use_12h', action='store_true', help='Use 12-hour time format')
    parser.add_argument('--24', dest='use_24h', action='store_true', help='Use 24-hour time format')
    parser.add_argument('-a', '--add', nargs=2, metavar=('LABEL', 'OFFSET'), action='append',
                        help='Add a clock with specified label and UTC offset')
    parser.add_argument('-r', '--remove', metavar='LABEL', action='append',
                        help='Remove a clock with specified label')
    args = parser.parse_args()
    if args.use_12h:
        clock.use_24h = False
        clock.config_modified = True
    if args.use_24h:
        clock.use_24h = True
        clock.config_modified = True
    if args.add:
        for label, offset in args.add:
            parsed_offset = clock.parse_offset(offset)
            if parsed_offset is not None:
                if clock.add_clock(label, parsed_offset):
                    clock.config_modified = True
    if args.remove:
        for label in args.remove:
            if clock.remove_clock(label):
                clock.config_modified = True
    if clock.config_modified:
        clock.save_config()

def main():
    clock = WorldClock()
    parse_args(clock)
    try:
        curses.wrapper(clock.run)
    except KeyboardInterrupt:
        if clock.config_modified:
            clock.save_config()
        print("\nGoodbye")

if __name__ == "__main__":
    main()
