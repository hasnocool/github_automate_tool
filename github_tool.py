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

# Utility Functions to check GitHub CLI installation and authentication
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

def list_gists():
    result = run_command(["gh", "gist", "list", "--json", "id,description,public"])
    if result:
        gists = json.loads(result)
        for gist in gists:
            print(f"Gist ID: {gist['id']}, Description: {gist['description']}, Public: {gist['public']}")
    else:
        print("Error retrieving Gists.")

def edit_gist(gist_id, file_path):
    result = run_command(["gh", "gist", "edit", gist_id, file_path])
    if result is None:
        print(f"Gist '{gist_id}' edited successfully.")
    else:
        print(f"Failed to edit Gist '{gist_id}'.")

def delete_gist(gist_id):
    result = run_command(["gh", "gist", "delete", gist_id])
    if result is None:
        print(f"Gist '{gist_id}' deleted successfully.")
    else:
        print(f"Failed to delete Gist '{gist_id}'.")

def list_notifications():
    result = run_command(["gh", "api", "notifications"])
    if result:
        notifications = json.loads(result)
        for notification in notifications:
            print(f"Notification: {notification['reason']}, Repository: {notification['repository']['full_name']}")
    else:
        print("Error retrieving notifications.")

def mark_notifications_as_read():
    result = run_command(["gh", "api", "-X", "PUT", "notifications"])
    if result is None:
        print("Marked all notifications as read.")
    else:
        print("Failed to mark notifications as read.")

def list_secrets(repo_name):
    result = run_command(["gh", "secret", "list", "--repo", repo_name])
    if result:
        print(result)
    else:
        print(f"No secrets found for repository '{repo_name}'.")

def add_secret(repo_name, secret_name, secret_value):
    result = run_command(["gh", "secret", "set", secret_name, "--body", secret_value, "--repo", repo_name])
    if result is None:
        print(f"Secret '{secret_name}' added to repository '{repo_name}'.")
    else:
        print(f"Failed to add secret '{secret_name}' to repository '{repo_name}'.")

def delete_secret(repo_name, secret_name):
    result = run_command(["gh", "secret", "remove", secret_name, "--repo", repo_name])
    if result is None:
        print(f"Secret '{secret_name}' deleted from repository '{repo_name}'.")
    else:
        print(f"Failed to delete secret '{secret_name}' from repository '{repo_name}'.")

def get_repo_stats(repo_name):
    result = run_command(["gh", "repo", "view", repo_name, "--json", "stargazerCount,forkCount,watchersCount"])
    if result:
        stats = json.loads(result)
        print(f"Stars: {stats['stargazerCount']}, Forks: {stats['forkCount']}, Watchers: {stats['watchersCount']}")
    else:
        print(f"Error retrieving statistics for repository '{repo_name}'.")

def create_release(repo_name, tag_name, title, notes):
    result = run_command(["gh", "release", "create", tag_name, "--title", title, "--notes", notes, "--repo", repo_name])
    if result is None:
        print(f"Release '{title}' created for repository '{repo_name}'.")
    else:
        print(f"Failed to create release for repository '{repo_name}'.")

def list_releases(repo_name):
    result = run_command(["gh", "release", "list", "--repo", repo_name])
    if result:
        print(result)
    else:
        print(f"Error retrieving releases for repository '{repo_name}'.")

def create_pull_request(repo_name, title, body, base="main", head="HEAD"):
    result = run_command(["gh", "pr", "create", "--title", title, "--body", body, "--base", base, "--head", head, "--repo", repo_name])
    if result is None:
        print(f"Pull request '{title}' created for repository '{repo_name}'.")
    else:
        print(f"Failed to create pull request for repository '{repo_name}'.")

def list_pull_requests(repo_name):
    result = run_command(["gh", "pr", "list", "--repo", repo_name, "--json", "title,number,state"])
    if result:
        pull_requests = json.loads(result)
        for pr in pull_requests:
            print(f"PR #{pr['number']}: {pr['title']} [{pr['state']}]")
    else:
        print(f"Error retrieving pull requests for repository '{repo_name}'.")

def create_issue(repo_name, title, body):
    result = run_command(["gh", "issue", "create", "--title", title, "--body", body, "--repo", repo_name])
    if result is None:
        print(f"Issue '{title}' created for repository '{repo_name}'.")
    else:
        print(f"Failed to create issue for repository '{repo_name}'.")

def list_issues(repo_name):
    result = run_command(["gh", "issue", "list", "--repo", repo_name, "--json", "title,number,state"])
    if result:
        issues = json.loads(result)
        for issue in issues:
            print(f"Issue #{issue['number']}: {issue['title']} [{issue['state']}]")
    else:
        print(f"Error retrieving issues for repository '{repo_name}'.")

def add_collaborator(repo_name, collaborator):
    result = run_command(["gh", "repo", "add-collaborator", collaborator, "--repo", repo_name])
    if result is None:
        print(f"Collaborator '{collaborator}' added to repository '{repo_name}'.")
    else:
        print(f"Failed to add collaborator '{collaborator}' to repository '{repo_name}'.")

def remove_collaborator(repo_name, collaborator):
    result = run_command(["gh", "repo", "remove-collaborator", collaborator, "--repo", repo_name])
    if result is None:
        print(f"Collaborator '{collaborator}' removed from repository '{repo_name}'.")
    else:
        print(f"Failed to remove collaborator '{collaborator}' from repository '{repo_name}'.")

# Custom HelpFormatter to append example usage at the end
class CustomHelpFormatter(argparse.HelpFormatter):
    def add_usage(self, usage, actions, groups, prefix=None):
        super(CustomHelpFormatter, self).add_usage(usage, actions, groups, prefix)
        self.add_examples()

    def add_examples(self):
        example_usage = '''
        \nExamples of usage:
        1. Clone a repository to a local directory:
           $ python script.py --clone https://github.com/user/repo.git /path/to/dir
           
        2. List all repositories for the authenticated user:
           $ python script.py --list
        
        3. Create a new branch in a repository:
           $ python script.py --create-branch feature-branch
        
        4. Create a pull request:
           $ python script.py --create-pr my-repo "Add new feature" "This adds a new feature"

        5. Enable a GitHub Actions workflow:
           $ python script.py --enable-action my-repo my-workflow.yml
        '''
        self.add_text(example_usage)

def main():
    parser = argparse.ArgumentParser(
        description="GitHub repository management tool",
        formatter_class=CustomHelpFormatter
    )
    
    # Define arguments as before
    parser.add_argument("--gist", help="Create a Gist from the specified file", metavar="FILE")
    parser.add_argument("--create", help="Create a new repository for the specified directory", metavar="DIR")
    parser.add_argument("--publish", help="Publish the specified folder to GitHub", metavar="FOLDER")
    parser.add_argument("--rename", nargs=2, metavar=('FOLDER', 'NEW_NAME'), help="Rename the specified folder and update GitHub")
    parser.add_argument("--update", nargs='?', const='.', default=None, metavar="DIR", help="Update the specified directory (default: current directory)")
    parser.add_argument("--message", "-m", help="Commit message for update", default="Update repository")
    parser.add_argument("--set-details", help="Set repository details", metavar="REPO_NAME")
    parser.add_argument("--description", help="Set repository description")
    parser.add_argument("--website", help="Set repository website")
    parser.add_argument("--topics", help="Set repository topics (space-separated)")

    # Define more arguments for the other functionalities
    parser.add_argument("--clone", help="Clone a GitHub repository to a local directory", nargs=2, metavar=("REPO_URL", "DEST_DIR"))
    parser.add_argument("--list", help="List all repositories with optional filter by visibility", metavar="VISIBILITY", nargs="?", const="all")
    parser.add_argument("--delete", help="Delete a specified GitHub repository", metavar="REPO_NAME")
    parser.add_argument("--create-branch", help="Create a new branch in the repository", metavar="BRANCH_NAME")
    parser.add_argument("--list-branches", help="List all branches in the current repository", action="store_true")
    parser.add_argument("--switch-branch", help="Switch to the specified branch", metavar="BRANCH_NAME")

    # Additional features
    parser.add_argument("--archive", help="Archive the specified repository", metavar="REPO_NAME")
    parser.add_argument("--unarchive", help="Unarchive the specified repository", metavar="REPO_NAME")
    parser.add_argument("--fork", help="Fork the specified repository", metavar="REPO_URL")
    parser.add_argument("--sync-fork", help="Sync a forked repository with upstream", metavar="REPO_NAME")
    parser.add_argument("--enable-pages", help="Enable GitHub Pages for the specified repository", metavar="REPO_NAME")
    parser.add_argument("--backup", help="Backup the specified repository", nargs=2, metavar=("REPO_NAME", "BACKUP_DIR"))
    parser.add_argument("--license", help="Manage the license for a repository", metavar="REPO_NAME")
    parser.add_argument("--license-type", help="Specify the license type for the repository", default="MIT")

    # More argument definitions for Gists, notifications, actions, PRs, issues, etc.
    parser.add_argument("--list-gists", help="List all Gists", action="store_true")
    parser.add_argument("--edit-gist", help="Edit the specified Gist", nargs=2, metavar=("GIST_ID", "FILE"))
    parser.add_argument("--delete-gist", help="Delete the specified Gist", metavar="GIST_ID")
    parser.add_argument("--list-notifications", help="List all notifications", action="store_true")
    parser.add_argument("--mark-notifications-read", help="Mark all notifications as read", action="store_true")
    parser.add_argument("--list-secrets", help="List all secrets in the specified repository", metavar="REPO_NAME")
    parser.add_argument("--add-secret", help="Add a secret to the specified repository", nargs=3, metavar=("REPO_NAME", "SECRET_NAME", "SECRET_VALUE"))
    parser.add_argument("--delete-secret", help="Delete a secret from the specified repository", nargs=2, metavar=("REPO_NAME", "SECRET_NAME"))
    parser.add_argument("--repo-stats", help="Get statistics for the specified repository", metavar="REPO_NAME")
    parser.add_argument("--create-release", help="Create a new release for the repository", nargs=3, metavar=("REPO_NAME", "TAG_NAME", "TITLE"))
    parser.add_argument("--list-releases", help="List all releases for the specified repository", metavar="REPO_NAME")
    parser.add_argument("--create-pr", help="Create a new pull request", nargs=3, metavar=("REPO_NAME", "TITLE", "BODY"))
    parser.add_argument("--list-prs", help="List all pull requests for the specified repository", metavar="REPO_NAME")
    parser.add_argument("--create-issue", help="Create a new issue for the repository", nargs=3, metavar=("REPO_NAME", "TITLE", "BODY"))
    parser.add_argument("--list-issues", help="List all issues for the specified repository", metavar="REPO_NAME")
    parser.add_argument("--add-collaborator", help="Add a collaborator to the repository", nargs=2, metavar=("REPO_NAME", "COLLABORATOR"))
    parser.add_argument("--remove-collaborator", help="Remove a collaborator from the repository", nargs=2, metavar=("REPO_NAME", "COLLABORATOR"))

    # GitHub Actions management
    parser.add_argument("--list-actions", help="List all GitHub Actions workflows for the specified repository", metavar="REPO_NAME")
    parser.add_argument("--run-action", help="Run the specified GitHub Action workflow", nargs=2, metavar=("REPO_NAME", "WORKFLOW_NAME"))
    parser.add_argument("--disable-action", help="Disable the specified GitHub Action workflow", nargs=2, metavar=("REPO_NAME", "WORKFLOW_NAME"))
    parser.add_argument("--enable-action", help="Enable the specified GitHub Action workflow", nargs=2, metavar=("REPO_NAME", "WORKFLOW_NAME"))

    args = parser.parse_args()

    # Ensure GitHub CLI is installed and authenticated
    check_gh_installed()
    check_gh_auth()

    # Call the appropriate function based on arguments
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
    elif args.set_details:
        set_repo_details(args.set_details, args.description, args.website, args.topics)

    # More conditions for additional functionality
    elif args.clone:
        clone_repo(args.clone[0], args.clone[1])
    elif args.list:
        list_repos(args.list)
    elif args.delete:
        delete_repo(args.delete)
    elif args.create_branch:
        create_branch(args.create_branch)
    elif args.list_branches:
        list_branches()
    elif args.switch_branch:
        switch_branch(args.switch_branch)

    # Additional functionality handling
    elif args.archive:
        archive_repo(args.archive)
    elif args.unarchive:
        archive_repo(args.unarchive, archive=False)
    elif args.fork:
        fork_repo(args.fork)
    elif args.sync_fork:
        sync_fork(args.sync_fork)
    elif args.enable_pages:
        enable_github_pages(args.enable_pages)
    elif args.backup:
        backup_repo(args.backup[0], args.backup[1])
    elif args.license:
        manage_license(args.license, args.license_type)

    # GitHub Actions management
    elif args.list_actions:
        list_actions(args.list_actions)
    elif args.run_action:
        run_workflow(args.run_action[0], args.run_action[1])
    elif args.disable_action:
        disable_workflow(args.disable_action[0], args.disable_action[1])
    elif args.enable_action:
        enable_workflow(args.enable_action[0], args.enable_action[1])

    else:
        parser.print_help()

if __name__ == "__main__":
    main()




