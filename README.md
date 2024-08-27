# Todo Manager

This is a terminal-based Todo Manager application written in Python, allowing you to manage tasks directly within a `README.md` file in your git repository. The application uses the `urwid` library for creating a text-based user interface (TUI). It reads todos from the `README.md` file, allowing you to mark them as done, open, or add new todos.

## Features

- **Git Integration**: Ensures that the application runs only inside a Git repository.
- **Automatic Todo Parsing**: Scans the `README.md` file for todo items listed under the "## Todo" section.
- **Todo Management**: 
  - View open and closed todos in a split view.
  - Add new todos.
  - Toggle the status of todos (open/closed).
  - Automatically update the `README.md` file with the latest todo list.
- **Keyboard Shortcuts**:
  - `j` / `down arrow`: Move down the list of todos.
  - `k` / `up arrow`: Move up the list of todos.
  - `h`: Switch focus to open todos.
  - `l`: Switch focus to closed todos.
  - `space`: Toggle the status of the selected todo.
  - `a`: Open a dialog to add a new todo.
  - `q`: Save and quit the application.

## Installation

### Prerequisites

- **Python 3.6+**
- **pip** (Python package installer)

### Dependencies

This project requires the following Python libraries:

- `urwid` — A library for creating terminal user interfaces with Python.
- `uuid` — For generating unique identifiers for each todo item.
- `subprocess` — For interacting with the git repository.

To install the dependencies, run:

```bash
pip install urwid
```

### Cloning and Running the Application

1. **Clone the Repository**:
   If you haven't already, clone the git repository where this application resides:

   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Running the Application**:

   Execute the script using Python:

   ```bash
   python todo_manager.py
   ```

   Replace `todo_manager.py` with the filename you saved the script as.

## How It Works

1. **Git Repository Check**:
   The application starts by verifying that it is inside a Git repository. If it's not, the application will exit with an error.

2. **README.md Check**:
   The script checks for a `README.md` file in the root of the repository. If the file doesn't contain a "## Todo" section, it prompts the user to add one.

3. **Todo Parsing**:
   The application parses the `README.md` file, extracting todos that are formatted as markdown tasks (e.g., `- [ ] Task name` for open tasks, `- [x] Task name` for closed tasks).

4. **User Interaction**:
   Users can navigate through the todos using keyboard shortcuts, add new tasks, or toggle the status of existing ones.

5. **Saving**:
   Upon quitting the application, the todo list in the `README.md` file is updated automatically.

## Adding Todos

When running the application, press `a` to add a new todo. Enter the text for your todo and press `Enter` to save it. The todo will be added to the "Open Todos" list.

## Modifying Todos

To mark a todo as done or reopen it, navigate to the todo and press `space`. This will toggle the todo's status between open and closed.

## Exiting

Press `q` to save all changes and exit the application. The `README.md` file will be updated with the latest state of your todo list.

## License

This project is open-source. Feel free to use, modify, and distribute it as per your needs.
