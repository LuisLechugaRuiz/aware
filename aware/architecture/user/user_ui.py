# TODO: Use a proper ui, probably the next version of https://github.com/mckaywrigley/chatbot-ui.
import argparse
import curses
import random

from aware.architecture.user.user import User
from aware.config.config import Config


class UserUI:
    def __init__(self, user: User):
        self.user = user
        self.num_colors = self.init_colors()  # Initialize colors and get the count
        self.user_colors = {"Aware": 1}  # Maps usernames to color pair numbers
        self.available_colors = list(
            range(2, self.num_colors + 1)
        )  # List of available color pair numbers

    def chat_ui(self, stdscr):
        curses.cbreak()
        stdscr.nodelay(True)
        height, width = stdscr.getmaxyx()
        chat_win = curses.newwin(height - 3, width, 0, 0)
        chat_win.scrollok(True)
        input_win = curses.newwin(3, width, height - 3, 0)
        input_buffer = ""
        prefix = "Enter message: "
        cursor_x, cursor_y = len(prefix), 0
        input_win_height = 10  # Height of input window
        last_displayed_msg_index = 0  # Index of the last displayed message

        while True:
            height, width = stdscr.getmaxyx()
            input_win.resize(input_win_height, width)
            input_win.mvwin(height - input_win_height, 0)

            # Update messages, window resizing, etc.
            # Only update if there are new messages
            if last_displayed_msg_index < len(self.user.incoming_messages):
                new_messages = self.user.incoming_messages[last_displayed_msg_index:]
                for msg in new_messages:
                    color_pair_number = self.get_user_color(msg.user_name)
                    # Add the username with color
                    chat_win.addstr(
                        f"{msg.user_name}", curses.color_pair(color_pair_number)
                    )
                    # Add the rest of the message in the default color
                    chat_win.addstr(f": {msg.message}\n\n")
                last_displayed_msg_index = len(self.user.incoming_messages)

            chat_win.refresh()

            # Non-blocking check for input
            char = stdscr.getch()
            if char != curses.ERR:
                if char == 10:  # Enter key
                    self.user.send_message(input_buffer)
                    input_buffer = ""
                    cursor_x, cursor_y = (
                        len(prefix),
                        0,
                    )  # Reset cursor position after the prefix
                elif char == 27:  # Escape key
                    break
                elif char in (8, 127, curses.KEY_BACKSPACE):
                    if cursor_x > 0 or cursor_y > 0:
                        input_buffer, cursor_x, cursor_y = self.delete_character(
                            input_buffer, cursor_x, cursor_y, len(prefix)
                        )
                elif char == curses.KEY_LEFT:
                    cursor_x, cursor_y = self.move_cursor_left(
                        input_buffer, cursor_x, cursor_y
                    )
                elif char == curses.KEY_RIGHT:
                    cursor_x, cursor_y = self.move_cursor_right(
                        input_buffer, cursor_x, cursor_y, width, len(prefix)
                    )
                else:
                    input_buffer, cursor_x, cursor_y = self.insert_character(
                        input_buffer,
                        chr(char),
                        cursor_x,
                        cursor_y,
                        width - len(prefix),
                        prefix,
                    )

                # Display the input buffer
                try:
                    input_win.clear()
                    self.display_input(
                        input_win,
                        input_buffer,
                        cursor_x,
                        cursor_y,
                        width - len(prefix),
                        input_win_height,
                        prefix,
                    )
                    input_win.refresh()
                except curses.error as e:
                    # Handle curses error (for debugging)
                    print(f"Curses error: {e}")

    def insert_character(self, buffer, char, x, y, max_width, prefix):
        lines = buffer.split("\n")

        # Ensure the current line exists
        while y >= len(lines):
            lines.append("")

        line = lines[y]

        # Adjust x to account for the prefix on the first line
        adjusted_x = x - len(prefix) if y == 0 else x

        # Check if inserting the character exceeds max_width
        if (len(line) + len(prefix) >= max_width and y == 0) or (
            len(line) >= max_width and y > 0
        ):
            # Split the line at max_width, accounting for the prefix on the first line
            split_index = max_width - len(prefix) if y == 0 else max_width
            next_line = line[split_index:]
            line = line[:split_index]

            # Update cursor position
            x = (
                len(prefix) if y == 0 else 0
            )  # Reset x to start of line, after prefix for first line
            x += len(char)  # Position cursor after the inserted character

            # Update the current and next lines
            if y < len(lines) - 1:
                # Add to the next existing line
                lines[y + 1] = char + next_line + lines[y + 1]
            else:
                # Create a new line
                lines.append(char + next_line)

            # Adjust y to the next line
            y += 1

            # Adjust x to the start of the next line, accounting for the prefix
            x = len(prefix)

        else:
            # Insert the character at the specified position
            if x == len(line) + len(prefix):
                # If the cursor is at the end of the line, append the character
                line += char
            else:
                line = line[:adjusted_x] + char + line[adjusted_x:]
            lines[y] = line
            x += 1

        return "\n".join(lines), x, y

    def delete_character(self, buffer, x, y, prefix_length):
        lines = buffer.split("\n")
        adjusted_x = (
            x - prefix_length if y == 0 else x
        )  # Adjust cursor position for prefix

        if adjusted_x > 0:
            # Deleting a character from the current line
            lines[y] = lines[y][: adjusted_x - 1] + lines[y][adjusted_x:]
            x -= 1  # Move cursor back one position
        elif y > 0:
            # Deleting a character from the end of the previous line
            previous_line_end = len(lines[y - 1])
            lines[y - 1] += lines.pop(y)  # Merge with previous line
            y -= 1
            x = previous_line_end  # Move cursor to the end of the merged line
        else:
            # At the start of the first line, no deletion occurs
            return buffer, x, y

        # Re-calculate adjusted_x after deletion
        adjusted_x = x - prefix_length if y == 0 else x

        # If the cursor is now beyond the end of the line, move it to the end
        if adjusted_x > len(lines[y]):
            x = len(lines[y]) + (prefix_length if y == 0 else 0)

        return "\n".join(lines), x, y

    def move_cursor_left(self, buffer, x, y):
        if x > 0:
            x -= 1
        elif y > 0:
            y -= 1
            lines = buffer.split("\n")
            x = len(lines[y]) + len(
                lines[y - 1]
            )  # Move to the end of the previous line
        return x, y

    def move_cursor_right(self, buffer, x, y, max_width, prefix_length):
        lines = buffer.split("\n")

        if y < len(lines) - 1:
            y += 1
            x = prefix_length  # Move to the start of the next line, after the prefix
        elif x < len(lines[y]) + prefix_length:
            x += 1

        return x, y

    def display_input(
        self, win, buffer, cursor_x, cursor_y, max_width, max_height, prefix
    ):
        lines = buffer.split("\n")

        wrapped_lines = []
        screen_cursor_y = 0
        screen_cursor_x = 0
        cursor_adjusted = False

        for line_idx, line in enumerate(lines):
            # Include prefix only for the first line
            line_to_process = prefix + line if line_idx == 0 else line

            while len(line_to_process) > max_width:
                # Determine the wrap point
                wrap_point = max_width if line_idx > 0 else max_width - len(prefix)
                wrapped_line = line_to_process[:wrap_point]
                line_to_process = line_to_process[wrap_point:]

                # Detect if a word is split and save it for the next line
                if line_to_process and not line_to_process[0].isspace():
                    # Find the last space character in the wrapped line
                    last_space = wrapped_line.rfind(" ")
                    if last_space >= 0:
                        wrapped_line = wrapped_line[:last_space]
                        line_to_process = (
                            line_to_process.strip() + line_to_process[last_space:]
                        )

                wrapped_lines.append(wrapped_line)

                # Update cursor position for wrapped lines (only once)
                if line_idx == cursor_y and not cursor_adjusted:
                    if cursor_x > len(wrapped_line):
                        cursor_x -= len(wrapped_line)
                        screen_cursor_y += 1
                    else:
                        # Adjust cursor_x to the beginning of the current word
                        cursor_x = (
                            wrapped_line.rfind(" ") + 1
                            if line_to_process
                            else len(wrapped_line)
                        )
                        screen_cursor_x = cursor_x + (
                            len(prefix) if line_idx == 0 else 0
                        )
                        cursor_adjusted = True

            wrapped_lines.append(line_to_process)
            if line_idx == cursor_y and not cursor_adjusted:
                screen_cursor_x = cursor_x + (len(prefix) if line_idx == 0 else 0)
                cursor_adjusted = True

            screen_cursor_y += 1

        # Handle the case where the buffer is empty (e.g., after sending a message)
        if not buffer.strip():
            cursor_x, cursor_y = (
                len(prefix),
                0,
            )  # Position cursor right after the prefix

        # Handle vertical scrolling
        start_line = max(0, len(wrapped_lines) - max_height)

        # Clear window and display lines
        win.clear()
        for i, line in enumerate(wrapped_lines[start_line : start_line + max_height]):
            win.addstr(i, 0, line)

        # Move cursor to the correct position on the screen
        screen_cursor_y = min(screen_cursor_y, max_height - 1)
        screen_cursor_x = min(screen_cursor_x, max_width - 1)
        win.move(screen_cursor_y, screen_cursor_x)

    def init_colors(self):
        curses.start_color()
        color_pairs = [
            (curses.COLOR_BLUE, curses.COLOR_BLACK),
            (curses.COLOR_RED, curses.COLOR_BLACK),
            (curses.COLOR_GREEN, curses.COLOR_BLACK),
            (curses.COLOR_YELLOW, curses.COLOR_BLACK),
            (curses.COLOR_MAGENTA, curses.COLOR_BLACK),
            (curses.COLOR_CYAN, curses.COLOR_BLACK),
            (curses.COLOR_WHITE, curses.COLOR_BLACK),
        ]

        for i, (fg, bg) in enumerate(color_pairs, start=1):
            curses.init_pair(i, fg, bg)

        return len(color_pairs)  # Return the number of color pairs initialized

    def get_user_color(self, user_name):
        # If the user already has a color pair number, return it
        if user_name in self.user_colors:
            return self.user_colors[user_name]

        # If all colors are used, reset the available colors list
        if not self.available_colors:
            self.available_colors = list(range(2, self.num_colors + 1))

        # Assign a random color pair number from the available colors
        chosen_color_pair_number = random.choice(self.available_colors)
        self.available_colors.remove(chosen_color_pair_number)
        self.user_colors[user_name] = chosen_color_pair_number

        return chosen_color_pair_number


def main(stdscr, user):
    # Initialize User UI with the pre-initialized User object
    ui = UserUI(user=user)

    # Start the chat UI
    ui.chat_ui(stdscr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="User configuration script.")
    parser.add_argument(
        "-a",
        "--assistant_ip",
        type=str,
        default=Config().assistant_ip,
        help="Assistant IP",
    )
    args = parser.parse_args()

    # Initialize User
    user = User(assistant_ip=args.assistant_ip)

    # Start curses application and pass the User object to main
    curses.wrapper(main, user)
