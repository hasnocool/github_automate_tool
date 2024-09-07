import os
import subprocess
import sys
import argparse
import json

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
    
    # Remove existing origin if it exists
    run_command(["git", "remote", "remove", "origin"], check=False)
    
    # Add new origin
    result = run_command(["git", "remote", "add", "origin", repo_url])
    if result is None:
        print(f"Failed to add remote origin {repo_url}")
        return False

    print(f"Successfully added remote origin {repo_url}")
    return True

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
        print("Initialized new git repository.")
    else:
        print("Local git repository already exists. Skipping initialization.")

    # Check if the repository exists on GitHub
    if repo_exists_on_github(dir_name):
        print(f"Repository '{dir_name}' already exists on GitHub.")
        link_choice = input("Do you want to link the local repository to the existing GitHub repository? (y/n): ").lower()
        if link_choice == 'y':
            if link_to_github(dir_name):
                print("Successfully linked to existing GitHub repository.")
            else:
                print("Failed to link to existing GitHub repository.")
                return
        else:
            print("Skipping linking to GitHub repository.")
            return
    else:
        create_choice = input(f"Repository '{dir_name}' doesn't exist on GitHub. Do you want to create it? (y/n): ").lower()
        if create_choice == 'y':
            result = run_command(["gh", "repo", "create", dir_name, "--public", "--source=."])
            if result is None:
                print(f"Failed to create repository '{dir_name}' on GitHub.")
                print("You may need to create the repository manually on GitHub and then link it.")
                return
            print(f"Repository '{dir_name}' created on GitHub.")
        else:
            print("Skipping GitHub repository creation.")
            return

    # Add all files in the directory
    run_command(["git", "add", "."])

    # Check if there are changes to commit
    status = run_command(["git", "status", "--porcelain"])
    if status:
        # Commit with an automatic message
        run_command(["git", "commit", "-m", "Automatic commit: Updated files"])
        print("Changes committed locally.")
    else:
        print("No changes to commit.")

    # Push to the default branch
    push_choice = input("Do you want to push changes to GitHub? (y/n): ").lower()
    if push_choice == 'y':
        result = run_command(["git", "push", "-u", "origin", get_default_branch()])
        if result is not None:
            print(f"Repository '{dir_name}' has been updated and pushed to GitHub.")
        else:
            print(f"Repository '{dir_name}' has been updated locally, but there was an issue pushing to GitHub.")
            print("You may need to push manually or check your GitHub permissions.")
    else:
        print("Skipping push to GitHub. You can push changes manually later.")

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