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

def extract_total_hour_month_day(_input):
    hour_regex  = re.compile(ur'([0-9]*[h H])')
    day_regex   = re.compile(ur'([0-9]*[d D])')
    week_regex  = re.compile(ur'([0-9]*[w W])')

    total_hours = 0

    hours_match = hour_regex.findall(_input)
    days_match  = day_regex.findall(_input)
    weeks_match = week_regex.findall(_input)

    if len(hours_match) > 0:
        val = hours_match[0][:1]
        if val.isdigit():
            total_hours += int(val)

    if len(days_match) > 0:
        val = days_match[0][:1]
        if val.isdigit():
            total_hours += int(days_to_hours(val))

    if len(weeks_match) > 0:
        val = weeks_match[0][:1]
        if val.isdigit():
            total_hours += int(weeks_to_hours(val))

    return(total_hours, hours_match, days_match, weeks_match)

def calc_work_in_milestone(_issues):
    totals = dict()
    total  = 0
    milestones = gh.issues.milestones.list(user=SHS, repo=repoName).all()
    for milestone in milestones:
        for issue in _issues:
            if hasattr(issue, "estimate_value"):
                total += issue.estimate_value
                if milestone.title in totals:
                    totals[milestone.title] += issue.estimate_value
                else:
                    totals[milestone.title] = issue.estimate_value

    return (total, totals)

def quick_provide_estimate(_issues):
    for issue in _issues:
        if hasattr(issue, "estimate_value") == False:

            valid_input_entered = False

            while not valid_input_entered:
                input = raw_input("Enter estimate for " + issue.title + "(" + issue.body + ")")

                parsed_hours = extract_total_hour_month_day(input)[0]

                if parsed_hours > 0:
                    issue.body += "\n~estimate:" + input
                    data = dict(body=issue.body)
                    gh.issues.update(issue.number, data, user=SHS, repo=repoName)
                    valid_input_entered = True
                else:
                    print "Invalid input must be in the format 1w2d3h, 2d3h, 3h, 1w, etc"


issues_global = gh.issues.list_by_repo(SHS, repoName).all()

for issue in issues_global :
    regex   = re.compile(ur'(~[0-9 a-z A-Z]*:[0-9 a-z A-Z]*)')
    matches = regex.findall(issue.body)
    params  = dict()

    for match in matches:
        match = match[1:]
        key_val = match.split(":")
        params[key_val[0]] = key_val[1]

    if("estimate" in params):
        setattr(issue, "estimate_literal", params["estimate"])
        setattr(issue, "estimate_value", extract_total_hour_month_day(params["estimate"]))

    setattr(issue, "params", params)

quick_provide_estimate(issues_global)

