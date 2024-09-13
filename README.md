# GitHub Repository Management Script

This Python script provides a convenient command-line interface for managing GitHub repositories. It simplifies common tasks such as creating repositories, publishing folders, updating content, and more.

## Features

- Create new GitHub repositories
- Publish local folders to GitHub
- Rename repositories and update GitHub
- Update existing repositories
- Create Gists from files
- Automatic handling of repository initialization and linking

## Prerequisites

- Python 3.6 or higher
- GitHub CLI (`gh`) installed and authenticated
- Git installed and configured

## Installation

1. Clone this repository or download the script file.
2. Ensure you have the required dependencies installed:
   ```
   pip install argparse
   ```
3. Make sure GitHub CLI is installed and authenticated:
   ```
   gh auth login
   ```

## Usage

The script provides several commands for different GitHub operations:

### Create a New Repository

```
python github_manager.py --create DIR
```
This creates a new repository for the specified directory.

### Publish a Folder to GitHub

```
python github_manager.py --publish FOLDER
```
This publishes the specified folder to GitHub, moving it from the experimental to the active directory.

### Rename a Folder and Update GitHub

```
python github_manager.py --rename FOLDER NEW_NAME
```
This renames the specified folder, updates the GitHub remote, and pushes the changes.

### Update an Existing Repository

```
python github_manager.py --update [DIR] -m "Commit message"
```
This updates the specified directory (or current directory if not specified) on GitHub.

### Create a Gist

```
python github_manager.py --gist FILE
```
This creates a Gist from the specified file.

## Options

- `--message` or `-m`: Specify a commit message for update operations.
- All directory arguments are optional and default to the current directory if not specified.

## Examples

1. Create a new repository for a project:
   ```
   python github_manager.py --create ~/projects/my_new_project
   ```

2. Update an existing repository:
   ```
   python github_manager.py --update -m "Updated documentation"
   ```

3. Rename a repository:
   ```
   python github_manager.py --rename ~/Github/old_name new_project_name
   ```

4. Create a Gist from a file:
   ```
   python github_manager.py --gist ~/documents/code_snippet.py
   ```

## Contributing

Contributions to improve the script are welcome. Please feel free to submit pull requests or open issues to suggest improvements or report bugs.

## License

This script is released under the MIT License. See the LICENSE file for details.