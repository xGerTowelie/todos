import sys
import os
import urwid
import re
import subprocess
import uuid
import signal

class Todo:
    def __init__(self, text, status="open"):
        self.id = str(uuid.uuid4())
        self.text = text
        self.status = status
        self.delete_dialog = None
        self.todo_to_delete = None

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
            if not re.search(r'^## Todo\s*$', content, re.MULTILINE):
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
            content = f.readlines()
        
        todo_section_start = None
        for i, line in enumerate(content):
            if line.strip() == "## Todo":
                todo_section_start = i + 1
                break
        
        if todo_section_start is not None:
            for line in content[todo_section_start:]:
                if line.startswith("#"):
                    break
                todo_match = re.match(r'- \[([ x])\] (.+)', line.strip())
                if todo_match:
                    status, text = todo_match.groups()
                    todo = Todo(text.strip(), "closed" if status == 'x' else "open")
                    self.todos[todo.status].append(todo)

    def save_todos(self):
        with open(self.readme_path, "r") as f:
            content = f.readlines()
        
        new_content = []
        in_todo_section = False
        for line in content:
            if line.strip() == "## Todo":
                new_content.append(line)
                in_todo_section = True
                for todo in self.todos["open"]:
                    new_content.append(f"- [ ] {todo.text}\n")
                for todo in self.todos["closed"]:
                    new_content.append(f"- [x] {todo.text}\n")
            elif in_todo_section and (line.startswith("#") or not line.strip()):
                in_todo_section = False
                new_content.append(line)
            elif not in_todo_section:
                new_content.append(line)
        
        with open(self.readme_path, "w") as f:
            f.writelines(new_content)

    def create_todo_list(self, todos):
        body = []
        for todo in todos:
            checkbox = self.checkbox_open if todo.status == "open" else self.checkbox_closed
            text = urwid.Text(f"{checkbox} {todo.text}")
            body.append(urwid.AttrMap(text, None, focus_map='focus'))
        return urwid.ListBox(urwid.SimpleFocusListWalker(body))

    def item_chosen(self, todo):
        old_status = todo.status
        new_status = "closed" if old_status == "open" else "open"
        self.todos[old_status].remove(todo)
        todo.status = new_status
        self.todos[new_status].append(todo)

        if not self.todos[old_status]:
            self.current_focus = new_status
            self.columns.focus_position = 0 if new_status == "open" else 1

        self.update_lists()

    def update_lists(self):
        open_todos = self.todos["open"]
        closed_todos = self.todos["closed"]

        self.open_todos.body[:] = self.create_todo_list(open_todos).body
        self.closed_todos.body[:] = self.create_todo_list(closed_todos).body

        if open_todos:
            self.open_todos.focus_position = min(self.open_todos.focus_position if self.open_todos.focus else 0, len(open_todos) - 1)

        if closed_todos:
            self.closed_todos.focus_position = min(self.closed_todos.focus_position if self.closed_todos.focus else 0, len(closed_todos) - 1)

        if self.current_focus == "open" and not open_todos:
            self.current_focus = "closed"
            self.columns.focus_position = 1
        elif self.current_focus == "closed" and not closed_todos:
            self.current_focus = "open"
            self.columns.focus_position = 0

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
        elif key == 'd':
            self.open_delete_dialog()

    def handle_delete_input(self, key):
        if key == 'enter':
            self.delete_todo()
        elif key == 'esc':
            self.close_delete_dialog()

    def open_delete_dialog(self):
        current_list = self.open_todos if self.current_focus == "open" else self.closed_todos
        if not current_list.body:
            return
        focus = current_list.focus
        if focus:
            index = current_list.focus_position
            self.todo_to_delete = self.todos[self.current_focus][index]
            question = urwid.Text(f"Are you sure you want to delete this todo?\n\n{self.todo_to_delete.text}\n\nPress Enter to confirm or Esc to cancel.")
            self.delete_dialog = urwid.Overlay(
                urwid.LineBox(question, title="Confirm Delete"),
                self.frame,
                align='center',
                width=('relative', 50),
                valign='middle',
                height='pack'
            )
            self.loop.widget = self.delete_dialog
            self.loop.unhandled_input = self.handle_delete_input

    def delete_todo(self):
        if self.todo_to_delete:
            self.todos[self.todo_to_delete.status].remove(self.todo_to_delete)
            self.update_lists()
        self.close_delete_dialog()

    def close_delete_dialog(self):
        self.loop.widget = self.frame
        self.loop.unhandled_input = self.unhandled_input
        self.todo_to_delete = None

    def close_delete_dialog(self, button=None):
        self.loop.widget = self.frame
        self.loop.unhandled_input = self.unhandled_input

    def swap_focus(self, new_focus):
        old_focus = self.current_focus
        old_list = self.open_todos if old_focus == "open" else self.closed_todos
        new_list = self.open_todos if new_focus == "open" else self.closed_todos

        if not self.todos[new_focus]:
            return

        old_position = old_list.focus_position if self.todos[old_focus] else 0
        new_position = min(old_position, len(new_list.body) - 1)

        self.current_focus = new_focus
        self.frame.focus_position = 'body'
        self.columns.focus_position = 0 if new_focus == "open" else 1
        new_list.focus_position = new_position

    def handle_movement(self, direction):
        current_list = self.open_todos if self.current_focus == "open" else self.closed_todos
        if not current_list.body:
            return
        if direction == 'up':
            current_list.focus_position = max(0, current_list.focus_position - 1)
        elif direction == 'down':
            current_list.focus_position = min(len(current_list.body) - 1, current_list.focus_position + 1)

    def toggle_current_todo(self):
        current_list = self.open_todos if self.current_focus == "open" else self.closed_todos
        if not current_list.body:
            return
        focus = current_list.focus
        if focus:
            index = current_list.focus_position
            todo = self.todos[self.current_focus][index]
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
        if text.strip():
            new_todo = Todo(text.strip())
            self.todos["open"].append(new_todo)
            self.update_lists()

    def main(self):
        if not self.check_git_repo():
            print("Error: Not a git repository.")
            sys.exit(1)

        if not self.check_readme():
            print("Error: README.md not found or user declined to add '## Todo' section.")
            sys.exit(1)

        self.parse_todos()

        self.open_todos = self.create_todo_list(self.todos["open"])
        self.closed_todos = self.create_todo_list(self.todos["closed"])

        open_box = urwid.LineBox(self.open_todos, title="Open Todos")
        closed_box = urwid.LineBox(self.closed_todos, title="Closed Todos")

        self.columns = urwid.Columns([open_box, closed_box])
        self.frame = urwid.Frame(self.columns)

        self.loop = urwid.MainLoop(self.frame, self.palette, unhandled_input=self.unhandled_input)

        def exit_on_ctrl_c(signum, frame):
            self.save_todos()
            raise urwid.ExitMainLoop()

        signal.signal(signal.SIGINT, exit_on_ctrl_c)

        self.loop.run()

if __name__ == "__main__":
    TodoApp().main()
