import sys
import os
import urwid
import re
import subprocess

class TodoApp:
    def __init__(self):
        self.todos = {"open": [], "closed": []}
        self.current_focus = "open"
        self.readme_path = "README.md"
        self.add_edit = None
        self.add_dialog = None
        self.palette = [
            ('body', 'dark cyan', ''),
            ('focus', 'black', 'white'),
            ('head', 'yellow', 'black'),
            ('foot', 'light cyan', 'black'),
        ]
        # Nerd Font checkbox icons
        self.checkbox_open = "\uf0c8"  # Empty checkbox
        self.checkbox_closed = "\uf14a"  # Checked checkbox

    def check_git_repo(self):
        try:
            subprocess.check_output(["git", "rev-parse", "--is-inside-work-tree"])
            return True
        except subprocess.CalledProcessError:
            return False

    def check_readme(self):
        if not os.path.exists(self.readme_path):
            with open(self.readme_path, "w") as f:
                f.write("# Project Name\n\n## Todo\n")
            return True

        with open(self.readme_path, "r") as f:
            content = f.read()
            if "## Todo" not in content:
                response = input("README.md exists but doesn't have a '## Todo' section. Add it? (y/n): ")
                if response.lower() == 'y':
                    with open(self.readme_path, "a") as f:
                        f.write("\n## Todo\n")
                    return True
                else:
                    return False
        return True

    def parse_todos(self):
        with open(self.readme_path, "r") as f:
            content = f.read()
            todos = re.findall(r'- \[([ x])\] (.+)', content)
            for status, text in todos:
                if status == 'x':
                    self.todos["closed"].append(text)
                else:
                    self.todos["open"].append(text)

    def save_todos(self):
        with open(self.readme_path, "r") as f:
            content = f.readlines()

        todo_section = False
        new_content = []
        for line in content:
            if line.strip() == "## Todo":
                todo_section = True
                new_content.append(line)
                for todo in self.todos["open"]:
                    new_content.append(f"- [ ] {todo}\n")
                for todo in self.todos["closed"]:
                    new_content.append(f"- [x] {todo}\n")
            elif todo_section and line.strip().startswith("- ["):
                continue
            else:
                new_content.append(line)
                todo_section = False

        with open(self.readme_path, "w") as f:
            f.writelines(new_content)

    def create_todo_list(self, todos, is_open=True):
        body = []
        for todo in todos:
            checkbox = self.checkbox_open if is_open else self.checkbox_closed
            text = urwid.Text(f"{checkbox} {todo}")
            body.append(urwid.AttrMap(text, None, focus_map='focus'))
        return urwid.ListBox(urwid.SimpleFocusListWalker(body))

    def item_chosen(self, todo):
        if todo in self.todos["open"]:
            self.todos["open"].remove(todo)
            self.todos["closed"].append(todo)
        else:
            self.todos["closed"].remove(todo)
            self.todos["open"].append(todo)
        self.update_lists()

    def update_lists(self):
        open_focus = self.open_todos.focus_position
        closed_focus = self.closed_todos.focus_position
        self.open_todos.body[:] = self.create_todo_list(self.todos["open"], True).body
        self.closed_todos.body[:] = self.create_todo_list(self.todos["closed"], False).body
        self.open_todos.focus_position = min(open_focus, len(self.open_todos.body) - 1)
        self.closed_todos.focus_position = min(closed_focus, len(self.closed_todos.body) - 1)

    def unhandled_input(self, key):
        if key in ('q', 'Q'):
            self.save_todos()
            raise urwid.ExitMainLoop()
        elif key in ('j', 'down'):
            self.handle_movement('down')
        elif key in ('k', 'up'):
            self.handle_movement('up')
        elif key == 'h':
            self.swap_focus("open")
        elif key == 'l':
            self.swap_focus("closed")
        elif key == ' ':
            self.toggle_current_todo()
        elif key == 'a':
            self.open_add_dialog()

    def swap_focus(self, new_focus):
        old_focus = self.current_focus
        old_list = self.open_todos if old_focus == "open" else self.closed_todos
        new_list = self.open_todos if new_focus == "open" else self.closed_todos
        
        old_position = old_list.focus_position
        new_position = min(old_position, len(new_list.body) - 1)
        
        self.current_focus = new_focus
        self.frame.focus_position = 'body'
        self.columns.focus_position = 0 if new_focus == "open" else 1
        new_list.focus_position = new_position

    def handle_movement(self, direction):
        current_list = self.open_todos if self.current_focus == "open" else self.closed_todos
        if direction == 'up':
            current_list.focus_position = max(0, current_list.focus_position - 1)
        elif direction == 'down':
            current_list.focus_position = min(len(current_list.body) - 1, current_list.focus_position + 1)

    def toggle_current_todo(self):
        current_list = self.open_todos if self.current_focus == "open" else self.closed_todos
        focus = current_list.focus
        if focus:
            todo = focus.base_widget.text.split(' ', 1)[1]
            self.item_chosen(todo)

    def open_add_dialog(self):
        self.add_edit = urwid.Edit("New todo: ")
        self.add_dialog = urwid.Overlay(
            urwid.LineBox(self.add_edit),
            self.frame,
            align='center',
            width=('relative', 80),
            valign='middle',
            height='pack'
        )
        self.loop.widget = self.add_dialog
        self.loop.unhandled_input = self.handle_add_input

    def handle_add_input(self, key):
        if key == 'enter':
            self.add_todo(self.add_edit.edit_text)
            self.close_add_dialog()
        elif key == 'esc':
            self.close_add_dialog()

    def close_add_dialog(self):
        self.loop.widget = self.frame
        self.loop.unhandled_input = self.unhandled_input

    def add_todo(self, text):
        if text.strip():  # Only add non-empty todos
            self.todos["open"].append(text.strip())
            self.update_lists()

    def main(self):
        if not self.check_git_repo():
            print("Error: Not a git repository.")
            sys.exit(1)

        if not self.check_readme():
            print("Error: README.md not found or user declined to add '## Todo' section.")
            sys.exit(1)

        self.parse_todos()

        self.open_todos = self.create_todo_list(self.todos["open"], True)
        self.closed_todos = self.create_todo_list(self.todos["closed"], False)

        open_box = urwid.LineBox(self.open_todos, title="Open Todos")
        closed_box = urwid.LineBox(self.closed_todos, title="Closed Todos")

        self.columns = urwid.Columns([open_box, closed_box])
        self.frame = urwid.Frame(self.columns)

        self.loop = urwid.MainLoop(self.frame, self.palette, unhandled_input=self.unhandled_input)
        self.loop.run()

if __name__ == "__main__":
    TodoApp().main()
