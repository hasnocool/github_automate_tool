import os
import subprocess
import sys
import argparse

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
    branch = run_command(["git", "config", "--get", "init.defaultBranch"])
    return branch if branch else "main"

def repo_exists_locally():
    return os.path.isdir(".git")

def repo_exists_on_github(repo_name):
    result = run_command(["gh", "repo", "view", repo_name], check=False)
    return result is not None

def create_repo(directory):
    if not os.path.isdir(directory):
        print(f"Error: Directory '{directory}' does not exist.")
        sys.exit(1)

    # Change to the specified directory
    os.chdir(directory)

    # Get the directory name
    dir_name = os.path.basename(os.path.abspath(directory))

    # Check if the repository already exists locally
    if not repo_exists_locally():
        run_command(["git", "init"])
    else:
        print("Local git repository already exists. Skipping initialization.")

    # Check if the repository exists on GitHub
    if not repo_exists_on_github(dir_name):
        result = run_command(["gh", "repo", "create", dir_name, "--public", "--source=.", "--remote=origin"])
        if result is None:
            print(f"Failed to create repository '{dir_name}' on GitHub. It might already exist.")
    else:
        print(f"Repository '{dir_name}' already exists on GitHub. Skipping creation.")

    # Add all files in the directory
    run_command(["git", "add", "."])

    # Check if there are changes to commit
    status = run_command(["git", "status", "--porcelain"])
    if status:
        # Commit with an automatic message
        run_command(["git", "commit", "-m", "Automatic commit: Updated files"])
    else:
        print("No changes to commit.")

    # Get the default branch name
    default_branch = get_default_branch()

    # Check if the branch already exists
    branches = run_command(["git", "branch"])
    if default_branch not in branches:
        run_command(["git", "checkout", "-b", default_branch])
    else:
        run_command(["git", "checkout", default_branch])

    # Push to the default branch
    result = run_command(["git", "push", "-u", "origin", default_branch])
    
    if result is not None:
        print(f"Repository '{dir_name}' has been updated and pushed to GitHub.")
    else:
        print(f"Repository '{dir_name}' has been updated locally, but there was an issue pushing to GitHub.")
        print("You may need to push manually or check your GitHub permissions.")

def create_gist(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exist.")
        sys.exit(1)

    gist_url = run_command(["gh", "gist", "create", file_path])
    if gist_url:
        print(f"Gist created successfully. URL: {gist_url}")
    else:
        print("There was an issue creating the Gist.")

def main():
    parser = argparse.ArgumentParser(description="GitHub repository initialization and Gist creation tool")
    parser.add_argument("--gist", help="Create a Gist from the specified file", metavar="FILE")
    parser.add_argument("--dir", help="Specify the directory to create a repository for", default=".")
    args = parser.parse_args()

    check_gh_installed()
    check_gh_auth()

    if args.gist:
        create_gist(args.gist)
    else:
        create_repo(args.dir)

if __name__ == "__main__":
    main()
