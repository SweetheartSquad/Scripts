__author__ = 'ryan'

from pygithub3 import Github
import sys
import copy

SHS = 'SweetheartSquad'

args = sys.argv

if len(args) < 3:
    sys.exit("Expected args Repository Name, Username, Password")

repo     = args[1]
username = args[2]
password = args[3]

auth = dict(login=username, password=password)
gh = Github(**auth)

milestones = gh.issues.milestones.list(user=SHS, repo=repo).all()

for milestone in milestones:
    issues = gh.issues.list_by_repo(user=SHS, repo=repo, milestone=milestone.number).all()
    for issue in issues:
        issue_copy = copy.deepcopy(issues)
        for iss in issue_copy:
            if iss.number == issue.number:
                issue_copy.remove(iss)
                break
        body = issue.body
        num_arr = []
        if "~dependsOn:" not in body:
            print "-----------------------------------"
            print "(" + milestone.title + ") " + issue.title + " (" + body + ")"
            print "-----------------------------------"
            print "Which of the following does this depend on?"
            for iss in issue_copy:
                print "******"
                print "(" + str(iss.number) + ")" + iss.title + " (" + iss.body + ")"
                num_arr.append(iss.number)
            valid = False
            while not valid:
                num = raw_input("Enter number of the issue issue")
                if num.lower() == "none" or int(num) in num_arr:
                    valid = True
                    data = dict(body=(issue.body + "\n" + "~dependsOn:" + str(num)).strip())
                    gh.issues.update(issue.number, data, user=SHS, repo=repo)
                    valid = True
                else:
                    print "Invalid issue"