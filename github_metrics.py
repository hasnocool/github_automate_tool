import os
import subprocess
from datetime import datetime
import shlex

def run_command(command, shell=False):
    try:
        if shell:
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        else:
            args = shlex.split(command)
            result = subprocess.run(args, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "N/A"

def analyze_repo(repo_path):
    os.chdir(repo_path)
    print(f"Analyzing repository: {repo_path}")

    # General Project Metrics
    print(f"Number of commits: {run_command('git rev-list --all --count')}")
    print(f"Number of branches: {run_command('git branch -a | wc -l', shell=True)}")
    print(f"Number of tags: {run_command('git tag | wc -l', shell=True)}")
    print(f"Number of files: {run_command('git ls-files | wc -l', shell=True)}")
    print(f"Number of directories: {run_command('git ls-files | xargs -n1 dirname | sort -u | wc -l', shell=True)}")
    
    lines_of_code = run_command("git ls-files | xargs wc -l | tail -n 1 | awk '{print $1}'", shell=True)
    print(f"Number of lines of code: {lines_of_code}")
    
    print(f"Number of bytes of code: {run_command('git ls-files | xargs cat | wc -c', shell=True)}")

    # Active branches
    active_branches = run_command("""
    git for-each-ref --sort=-committerdate refs/heads/ --format='%(refname:short)' | 
    while read branch; do 
        if [ "$(git log -1 --since='3 months ago' -s $branch)" ]; then 
            echo $branch; 
        fi; 
    done | wc -l
    """, shell=True)
    print(f"Number of active branches (updated in last 3 months): {active_branches}")

    # Longest active branch
    current_timestamp = int(datetime.now().timestamp())
    longest_branch = run_command(f"""
    git for-each-ref --sort=-committerdate --format='%(refname:short)|%(committerdate:unix)' refs/heads/ | 
    while IFS='|' read branch date; do 
        echo "$branch|$(( ({current_timestamp} - $date) / 86400 ))"; 
    done | sort -t'|' -k2 -nr | head -n1
    """, shell=True)
    print(f"Longest active branch (days): {longest_branch}")

    # File sizes
    largest_file = run_command("""
    git ls-files | xargs -I{} git ls-files -s {} | 
    sort -k2 -nr | head -n1 | awk '{print $4 " (" $2 " bytes)"}'
    """, shell=True)
    smallest_file = run_command("""
    git ls-files | xargs -I{} git ls-files -s {} | 
    sort -k2 -n | head -n1 | awk '{print $4 " (" $2 " bytes)"}'
    """, shell=True)
    print(f"Largest file (by size): {largest_file}")
    print(f"Smallest file (by size): {smallest_file}")

    print(f"Largest directory (by size): {run_command('du -sh * | sort -rh | head -n1', shell=True)}")
    
    ignored_files = run_command("git status --ignored --porcelain | grep '^!!' | wc -l", shell=True)
    print(f"Number of ignored files: {ignored_files}")

    # Commit Metrics
    print(f"Number of commits in last day: {run_command('git rev-list --count --since=1.day HEAD')}")
    print(f"Number of commits in last week: {run_command('git rev-list --count --since=1.week HEAD')}")
    print(f"Number of commits in last month: {run_command('git rev-list --count --since=1.month HEAD')}")
    print(f"Number of commits in last year: {run_command('git rev-list --count --since=1.year HEAD')}")

    print("Number of commits by author:")
    print(run_command('git shortlog -sn --all'))

    print("Number of commits by day of week:")
    print(run_command('git log --format="%ad" --date=format:"%A" | sort | uniq -c | sort -nr', shell=True))

    avg_commit_msg_length = run_command("git log --format=%s | awk '{ sum += length($0); n++ } END { if (n > 0) print sum / n; }'", shell=True)
    print(f"Average commit message length: {avg_commit_msg_length}")

    longest_commit_msg = run_command("git log --format=%s | awk '{ if (length($0) > max) max = length($0) } END { print max }'", shell=True)
    print(f"Longest commit message: {longest_commit_msg}")

    shortest_commit_msg = run_command("git log --format=%s | awk '{ if (min == 0 || length($0) < min) min = length($0) } END { print min }'", shell=True)
    print(f"Shortest commit message: {shortest_commit_msg}")

    avg_commit_size = run_command("git log --stat --oneline | awk '/^ [0-9]/ { s+=$1+$4; n++ } END { if (n > 0) print s/n }'", shell=True)
    print(f"Average commit size (lines changed): {avg_commit_size}")

    fix_commits = run_command("git log --oneline | grep -ci 'fix' || echo 0", shell=True)
    print(f"Number of commits with 'fix' in message: {fix_commits}")

    empty_commits = run_command("git log --format=%s | grep -c '^$' || echo 0", shell=True)
    print(f"Number of commits with empty message: {empty_commits}")

    merge_commits = run_command('git log --merges --oneline | wc -l', shell=True)
    print(f"Number of merge commits: {merge_commits}")

    # Branch Metrics
    print(f"Number of merged branches: {run_command('git branch --merged | wc -l', shell=True)}")
    
    stale_branches = run_command("""
    git for-each-ref --sort=-committerdate --format="%(refname:short)" refs/heads/ | 
    while read branch; do 
        if [ -z "$(git log -1 --since="3 months ago" -s $branch)" ]; then 
            echo $branch; 
        fi; 
    done | wc -l
    """, shell=True)
    print(f"Number of stale branches (no activity in 3 months): {stale_branches}")
    
    avg_branch_lifespan = run_command("""
    git for-each-ref --format='%(refname:short)|%(creatordate:unix)|%(committerdate:unix)' refs/heads/ | 
    awk -F'|' '{ if ($3 != "") print ($3 - $2) / 86400 }' | 
    awk '{ sum += $1; n++ } END { if (n > 0) print sum / n; }'
    """, shell=True)
    print(f"Average lifespan of a branch before merging (days): {avg_branch_lifespan}")

    # Pull Request and Issue Metrics (if using GitHub CLI)
    if subprocess.call(['which', 'gh'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
        print(f"Number of open pull requests: {run_command('gh pr list --state open --limit 1000 | wc -l', shell=True)}")
        print(f"Number of closed pull requests: {run_command('gh pr list --state closed --limit 1000 | wc -l', shell=True)}")
        print(f"Number of open issues: {run_command('gh issue list --state open --limit 1000 | wc -l', shell=True)}")
        print(f"Number of closed issues: {run_command('gh issue list --state closed --limit 1000 | wc -l', shell=True)}")
    else:
        print("GitHub CLI not found. Skipping pull request and issue metrics.")

    # Contributor Metrics
    print(f"Number of contributors: {run_command('git shortlog -sn --all | wc -l', shell=True)}")
    print(f"Most active contributor: {run_command('git shortlog -sn --all | sort -rn | head -n1', shell=True)}")
    contributors_3_months = run_command('git shortlog -sn --since="3 months ago" | wc -l', shell=True)
    print(f"Number of contributors in last 3 months: {contributors_3_months}")

    print("------------------------")

# Main execution
repo_dir = os.path.expanduser("~/Github/active")
for dir_name in os.listdir(repo_dir):
    full_path = os.path.join(repo_dir, dir_name)
    if os.path.isdir(full_path) and os.path.exists(os.path.join(full_path, ".git")):
        analyze_repo(full_path)