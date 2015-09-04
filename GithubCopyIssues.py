__author__ = 'ryan'

from pygithub3 import Github
import sys

# Script to copy milestones and issues from one project to another
# Takes arguments in the following order from_repo, to_repo, username, password

SHS = 'SweetheartSquad'

args = sys.argv

if len(args) > 4:

    repo_from = args[1]
    repo_to   = args[2]
    username  = args[3]
    password  = args[4]

    auth = dict(login=username, password=password)
    gh = Github(**auth)

    milestones = gh.issues.milestones.list(user=SHS, repo=repo_from).all()
    issues = gh.issues.list_by_repo(SHS, repo_from).all()

    map_milestones = dict()

    for milestone in milestones:
        result = gh.issues.milestones.create(dict(title = milestone.title,
                                         state = milestone.state,
                                         description = milestone.description,
                                         due_on = milestone.due_on),
                                         SHS,
                                         repo_to)
        map_milestones[milestone.number] = result

    for issue in issues:
        gh.issues.create(dict(title=issue.title,
                              body=issue.body,
                              milestone=map_milestones[issue.milestone.number].number,
                              assignee=issue.assignee,
                              labels=issue.labels),
                        SHS,
                        repo_to)

else:
    print "Expected four arguments - from_repo, to_repo, username and password"