# WurlClock - Terminal World Clock

WurlClock is a world clock for your terminal. It's built on curses and is so simple there is no automatic handling of Daylight Savings Time! The curses library used isn't really supported by windows, nor is the location of the config file. Mac should work? Intended for linux systems.

---

## Features

- Display multiple clocks with custom labels and UTC offsets
- Support for local system time as well as fixed UTC offsets
- Persistent configuration saved in JSON format at `~/.config/wurlclock.json`
- Keyboard-driven interface with menu navigation and help screen
- Command-line options to add or remove clocks and set time format on launch

---

## Installation

1. Ensure Python 3 is installed on your system.

2. Clone or download this repository.

3. Run the script directly using Python:

```bash
python wurlclock.py
```
Installing dependancies varies a lot by OS so I will not explain.

## Usage

Launch the application in your terminal. The interface is controlled entirely via keyboard inputs:
Keybindings

- `q` or `Ctrl+C` — Quit the program

- `m` or `Enter` — Open the main menu

- `Esc` — Return to clock view or cancel menu actions

- `h` — Open the help screen

## Main Menu Options

- Add clock — Add a new clock by entering label and UTC offset

- Remove clock — Remove an existing clock from the list

- Options — Toggle 24-hour format and weekday display

- Help — Show help information

- Back to clock — Return to the main clock view

## Command Line Options

- `--12` — Use 12-hour time format on startup

- `--24` — Use 24-hour time format on startup

- `-a` LABEL OFFSET — Add a clock with label and UTC offset (can be specified multiple times)

- `-r` LABEL — Remove a clock by label (can be specified multiple times)

## Examples:

`python wurlclock.py --24 -a "New York" -5 -a "London" 0`
`python wurlclock.py --12 -r "Tokyo"`

## Configuration

Settings and clocks are saved in JSON format at:

`~/.config/wurlclock.json`

This file is automatically created and updated when you modify clocks or options.
Supported UTC Offset Formats

- Integer or decimal hours (e.g., +3, -5.5)

- Hours and minutes separated by colon (e.g., -3:30)

- you can also input `local` instead of an offset to use your system's local time

Note: Daylight Saving Time (DST) is not supported; offsets are fixed.

## Dependencies

- Python 3.x

- Standard Python libraries (curses, argparse, json, etc.)

This application is intended for use in a terminal supporting curses. Functionality and display may vary depending on terminal emulator capabilities.
