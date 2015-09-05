__author__ = 'ryan'

from pygithub3 import Github
import sys
import re

SHS = 'SweetheartSquad'

HOURS_IN_WORK_DAY = 8
DAYS_IN_WORK_WEEK = 5

def weeks_to_hours(weeks):
    return HOURS_IN_WORK_DAY * DAYS_IN_WORK_WEEK * int(weeks)

def days_to_hours(days):
    return HOURS_IN_WORK_DAY * int(days)

args = sys.argv

if len(args) < 3:
    sys.exit("Expected args Repository Name, Username, Password")

repoName = args[1]
username = args[2]
password = args[3]

auth = dict(login=username, password=password)
gh = Github(**auth)

def calc_work_in_milestone(issues):
    totals = dict()
    total  = 0
    milestones = gh.issues.milestones.list(user=SHS, repo=repoName).all()
    for milestone in milestones:
        for issue in issues:
            if hasattr(issue, "estimate_value"):
                total += issue.estimate_value
                if milestone.title in totals:
                    totals[milestone.title] += issue.estimate_value
                else:
                    totals[milestone.title] = issue.estimate_value

    return (total, totals)

issues = gh.issues.list_by_repo(SHS, repoName).all()

for issue in issues :
    regex   = re.compile(ur'(~[0-9 a-z A-Z]*:[0-9 a-z A-Z]*)')
    matches = regex.findall(issue.body)
    params  = dict()

    for match in matches:
        match = match[1:]
        key_val = match.split(":")
        params[key_val[0]] = key_val[1]

    if("estimate" in params):
        setattr(issue, "estimate_literal", params["estimate"])

        hour_regex  = re.compile(ur'([0-9]*[h H])')
        day_regex   = re.compile(ur'([0-9]*[d D])')
        week_regex  = re.compile(ur'([0-9]*[w W])')

        total_hours = 0

        hours_match = hour_regex.findall(params["estimate"])
        days_match  = day_regex.findall(params ["estimate"])
        weeks_match = week_regex.findall(params["estimate"])

        if len(hours_match) > 0:
            total_hours += int(hours_match[0][:1])

        if len(days_match) > 0:
            total_hours += int(days_to_hours(days_match[0][:1]))

        if len(weeks_match) > 0:
            total_hours += int(weeks_to_hours(weeks_match[0][:1]))

        setattr(issue, "estimate_value", int(total_hours))

    setattr(issue, "params", params)


