import os
import subprocess
import sys
import argparse
import json
import shutil

def run_command(command, cwd=None, check=True):
    try:
        result = subprocess.run(command, text=True, capture_output=True, cwd=cwd, check=check)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {' '.join(command)}")
        print(f"Error message: {e.stderr.strip()}")
        return None

def check_gh_installed():
    if run_command(["gh", "--version"], check=False) is None:
        print("GitHub CLI (gh) is not installed. Please install it first.")
        sys.exit(1)

def check_gh_auth():
    if run_command(["gh", "auth", "status"], check=False) is None:
        print("You are not authenticated with GitHub CLI. Please run 'gh auth login' first.")
        sys.exit(1)

def get_default_branch():
    return run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"]) or "main"

def repo_exists_locally():
    return os.path.isdir(".git")

def get_github_username():
    return run_command(["gh", "api", "user", "-q", ".login"])

def get_github_repos():
    result = run_command(["gh", "repo", "list", "--json", "name", "--limit", "1000"])
    if result:
        try:
            return [repo['name'] for repo in json.loads(result)]
        except json.JSONDecodeError:
            print("Error parsing GitHub repository list.")
    return []

def repo_exists_on_github(repo_name):
    return repo_name in get_github_repos()

def link_to_github(dir_name):
    username = get_github_username()
    if not username:
        print("Failed to get GitHub username. Please check your GitHub CLI authentication.")
        return False

    repo_url = f"https://github.com/{username}/{dir_name}.git"
    print(f"Attempting to link local repository to {repo_url}")
    
    run_command(["git", "remote", "remove", "origin"], check=False)
    result = run_command(["git", "remote", "add", "origin", repo_url])
    if result is None:
        print(f"Failed to add remote origin {repo_url}")
        return False

    print(f"Successfully added remote origin {repo_url}")
    return True

def get_full_path(folder_name):
    if os.path.isabs(folder_name):
        return folder_name
    return os.path.join(os.path.expanduser("~"), "Github", "experimental", folder_name)

def publish_repo(folder_path):
    if not os.path.isdir(folder_path):
        print(f"Error: Directory '{folder_path}' does not exist.")
        sys.exit(1)

    os.chdir(folder_path)
    dir_name = os.path.basename(os.path.abspath(folder_path))

    if not repo_exists_locally():
        run_command(["git", "init"])
        print("Initialized new git repository.")

    if not repo_exists_on_github(dir_name):
        result = run_command(["gh", "repo", "create", dir_name, "--public", "--source=."])
        if result is None:
            print(f"Failed to create repository '{dir_name}' on GitHub.")
            sys.exit(1)
        print(f"Repository '{dir_name}' created on GitHub.")
    else:
        print(f"Repository '{dir_name}' already exists on GitHub. Linking local repository.")
        if not link_to_github(dir_name):
            sys.exit(1)

    run_command(["git", "add", "."])
    run_command(["git", "commit", "-m", "Initial commit"])
    run_command(["git", "push", "-u", "origin", get_default_branch()])
    print(f"Repository '{dir_name}' has been pushed to GitHub.")

    active_path = os.path.join(os.path.expanduser("~"), "Github", "active")
    new_path = os.path.join(active_path, dir_name)
    
    os.makedirs(active_path, exist_ok=True)
    shutil.move(folder_path, new_path)
    print(f"Moved '{dir_name}' to {new_path}")

    os.chdir(active_path)
    clone_result = run_command(["git", "clone", f"https://github.com/{get_github_username()}/{dir_name}.git"])
    
    if clone_result is not None:
        print(f"Successfully cloned repository to {new_path}")
        shutil.rmtree(new_path)
        print(f"Removed original folder: {new_path}")
    else:
        print(f"Failed to clone repository. The original folder remains at {new_path}")

def create_gist(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exist.")
        sys.exit(1)

    gist_url = run_command(["gh", "gist", "create", file_path])
    if gist_url:
        print(f"Gist created successfully. URL: {gist_url}")
    else:
        print("There was an issue creating the Gist.")

def create_repo(directory):
    if not os.path.isdir(directory):
        print(f"Error: Directory '{directory}' does not exist.")
        sys.exit(1)

    os.chdir(directory)
    dir_name = os.path.basename(os.path.abspath(directory))

    if not repo_exists_locally():
        run_command(["git", "init"])
        print("Initialized new git repository.")

    if not repo_exists_on_github(dir_name):
        result = run_command(["gh", "repo", "create", dir_name, "--public", "--source=."])
        if result is None:
            print(f"Failed to create repository '{dir_name}' on GitHub.")
            sys.exit(1)
        print(f"Repository '{dir_name}' created on GitHub.")
    else:
        print(f"Repository '{dir_name}' already exists on GitHub. Linking local repository.")
        if not link_to_github(dir_name):
            sys.exit(1)

    run_command(["git", "add", "."])
    run_command(["git", "commit", "-m", "Initial commit"])
    run_command(["git", "push", "-u", "origin", get_default_branch()])
    print(f"Repository '{dir_name}' has been created and pushed to GitHub.")

def rename_folder(folder_path, new_name):
    if not os.path.isdir(folder_path):
        print(f"Error: Directory '{folder_path}' does not exist.")
        sys.exit(1)

    os.chdir(folder_path)
    old_name = os.path.basename(os.path.abspath(folder_path))
    parent_dir = os.path.dirname(folder_path)
    new_path = os.path.join(parent_dir, new_name)

    os.rename(folder_path, new_path)
    print(f"Renamed folder from '{old_name}' to '{new_name}'")

    run_command(["git", "remote", "set-url", "origin", f"https://github.com/{get_github_username()}/{new_name}.git"])

    run_command(["git", "add", "."])
    run_command(["git", "commit", "-m", f"Renamed repository from {old_name} to {new_name}"])
    run_command(["git", "push", "-u", "origin", get_default_branch()])
    print(f"Changes pushed to GitHub with new name '{new_name}'")

def update_repo(directory, commit_message):
    if not os.path.isdir(directory):
        print(f"Error: Directory '{directory}' does not exist.")
        sys.exit(1)

    os.chdir(directory)

    if not repo_exists_locally():
        print("Initializing new git repository.")
        run_command(["git", "init"])

    dir_name = os.path.basename(os.path.abspath(directory))

    if not repo_exists_on_github(dir_name):
        print(f"Creating new repository '{dir_name}' on GitHub.")
        result = run_command(["gh", "repo", "create", dir_name, "--public", "--source=."])
        if result is None:
            print(f"Failed to create repository '{dir_name}' on GitHub.")
            sys.exit(1)
    else:
        print(f"Repository '{dir_name}' already exists on GitHub. Ensuring local repository is linked.")
        link_to_github(dir_name)

    run_command(["git", "add", "."])
    run_command(["git", "commit", "-m", commit_message])
    
    branch = get_default_branch()
    push_result = run_command(["git", "push", "-u", "origin", branch])
    
    if push_result is None:
        print(f"Failed to push to GitHub. Trying to pull and merge changes.")
        run_command(["git", "pull", "--rebase", "origin", branch])
        push_result = run_command(["git", "push", "-u", "origin", branch])
        
        if push_result is None:
            print("Still unable to push. Please resolve conflicts manually.")
            sys.exit(1)

    print(f"Changes in '{directory}' have been committed and pushed to GitHub.")

def main():
    parser = argparse.ArgumentParser(description="GitHub repository management tool")
    parser.add_argument("--gist", help="Create a Gist from the specified file", metavar="FILE")
    parser.add_argument("--create", help="Create a new repository for the specified directory", metavar="DIR")
    parser.add_argument("--publish", help="Publish the specified folder to GitHub", metavar="FOLDER")
    parser.add_argument("--rename", nargs=2, metavar=('FOLDER', 'NEW_NAME'), help="Rename the specified folder and update GitHub")
    parser.add_argument("--update", nargs='?', const='.', default=None, metavar="DIR", help="Update the specified directory (default: current directory)")
    parser.add_argument("--message", "-m", help="Commit message for update", default="Update repository")
    args = parser.parse_args()

    check_gh_installed()
    check_gh_auth()

    if args.gist:
        create_gist(args.gist)
    elif args.create:
        create_repo(args.create)
    elif args.publish:
        full_path = get_full_path(args.publish)
        publish_repo(full_path)
    elif args.rename:
        rename_folder(args.rename[0], args.rename[1])
    elif args.update is not None:
        update_repo(args.update, args.message)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()