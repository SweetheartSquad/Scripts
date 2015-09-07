__author__ = 'ryan'

from pygithub3 import Github
import sys

SHS = 'SweetheartSquad'

args = sys.argv

if len(args) < 3:
    sys.exit("Expected args Repository Name, Username, Password")

repo     = args[1]
username = args[2]
password = args[3]

auth = dict(login=username, password=password)
gh = Github(**auth)

issues = gh.issues.list_by_repo(user=SHS, repo=repo).all()

for issue in issues:
    assignee = None
    valid = False
    if issue.assignee is None:
        while not valid:
            assignee = raw_input("Enter assignee for (" + issue.milestone.title + ") " + issue.title + "(" + issue.body + ")")
            try:
                gh.users.get(user=assignee)
                valid = True
                data = dict(assignee=assignee)
                gh.issues.update(issue.number, data, user=SHS, repo=repo)
            except Exception:
                print "Invalid user"
                pass