__author__ = 'ryan'

from pygithub3 import Github
import sys
import re
import copy

HOURS_IN_WORK_DAY = 8
DAYS_IN_WORK_WEEK = 5

mult = 10.0

startTime = 0
endTime = 500
now = 6

GANTT_BEGIN = '''
\\documentclass[tikz]{standalone}
\\usepackage{pgfgantt}
% set default font to Helvetica
\\RequirePackage[scaled]{helvet}
\\renewcommand\\familydefault{\\sfdefault}
\\RequirePackage[T1]{fontenc}
% colours from SweetHeart Squad logo
\\definecolor{shs1}{RGB}{169,55,216}
\\definecolor{shs2}{RGB}{255,140,205}
\\definecolor{shs3}{RGB}{209,52,131}
\\definecolor{shs5}{RGB}{216,128,255}

\\begin{document}
\\begin{ganttchart}[
y unit chart = 15,
y unit title = 15,
hgrid,
vgrid,
canvas/.append style={fill=none, draw=none, line width=.75pt},
% title
title/.style={draw=none, fill=none},
title label font=\\bfseries\\footnotesize,
title label node/.append style={below=7pt},
include title in canvas=false,
% task bars
bar label font=\\mdseries\\small\\color{black!70},
bar label node/.append style={left=2cm},
bar height=0.5,
bar/.append style={draw=none, fill=shs3},
bar incomplete/.append style={fill=shs2!25},
% feature groups
group/.append style={fill=shs3},
group incomplete/.append style={fill=shs2},
group left shift=0,
group right shift=0,
group height=0.8,
group label node/.append style={left=.6cm},
% milestones
milestone inline label node/.append style={left=5mm},
milestone/.append style={fill=black, rounded corners=0pt},
milestone height=1,
% milestone width=1,
% "today" line
today=''' + str(now) + ''',
today rule/.style={
  draw=shs3,
  dash pattern=on 1.5pt off 0.5pt,
  line width=1pt
}]{''' + str(startTime) + '''}{''' + str(endTime) + '''}
\\gantttitle{Weeks}{''' + str(endTime) + '''}\\\\
\\gantttitlelist{''' + str(startTime) + ''',...,''' + str(int(endTime/mult)) + '''}{'''+str(int(mult))+'''}\\\\
'''

def weeks_to_hours(weeks):
    return HOURS_IN_WORK_DAY * DAYS_IN_WORK_WEEK * float(weeks)

def days_to_hours(days):
    return HOURS_IN_WORK_DAY * float(days)

args = sys.argv

if len(args) < 4:
    sys.exit("Expected args Repository Name, Username, Password")

repoOwnerName = args[1]
repoName = args[2]
username = args[3]
password = args[4]

auth = dict(login=username, password=password)
gh = Github(**auth)


def extract_total_hour_month_day(_input):
    hour_regex  = re.compile(ur'([0-9]*[h H])')
    day_regex   = re.compile(ur'([0-9]*[d D])')
    week_regex  = re.compile(ur'([0-9]*[w W])')

    total_hours = 0
    
    # truncate argument list to the first element
    _input = _input[0]
    
    hours_match = hour_regex.findall(_input)
    days_match  = day_regex.findall(_input)
    weeks_match = week_regex.findall(_input)

    if len(hours_match) > 0:
        val = hours_match[0][:1]
        if val.isdigit():
            total_hours += float(val)

    if len(days_match) > 0:
        val = days_match[0][:1]
        if val.isdigit():
            total_hours += float(days_to_hours(val))

    if len(weeks_match) > 0:
        val = weeks_match[0][:1]
        if val.isdigit():
            total_hours += float(weeks_to_hours(val))

    return(total_hours, hours_match, days_match, weeks_match)


def get_extra_attributes(_object):
    params  = dict()
    #regex   = re.compile(ur'(~[0-9 a-z A-Z]*):((#?[0-9 a-z A-Z]*[;]?)*)')
    regex   = re.compile(ur'~([0-9 a-z A-Z]*):\s?([#0-9a-zA-Z;]*)')

    matches = []

    src  = None
    if hasattr(_object, "body"):
        if _object.body is not None:
            src = _object.body
    else:
        if _object.description is not None:
            src = _object.description
            
    print "Src: " + str(src.encode('ascii', 'ignore')) + "\n"
            
    matches = regex.findall(src)

    print "Matches: " + str(matches) + "\n"
    
    # if the regex didn't capture any arguments, return None early
    if len(matches) == 0:
        return None
    
    for match in matches:
        key_val = match[0]
        params[key_val] = match[1].replace("#","").split(";")
    
    
    print "Params: " + str(params) + "\n"
    
    return params


def calc_totals_for_issues(_issues):
    for issue in _issues :
        params = get_extra_attributes(issue)
        if("estimate" in params):
            setattr(issue, "estimate_literal", params["estimate"])
            setattr(issue, "estimate_value", extract_total_hour_month_day(params["estimate"])[0])

        setattr(issue, "params", params)
    return _issues


def calc_work_in_milestone(_milestone_issues):
    totals = dict()
    total  = 0
    for issue in _milestone_issues:
        if hasattr(issue, "estimate_value"):
            total += issue.estimate_value

    return total


def calc_dependent_offsets(_objects):
    total_obs = len(_objects)
    solved_objects = []
    unsolved_objects = []
    while len(_objects) > 0:
        object = _objects[len(_objects)-1]
        params = get_extra_attributes(object)
        if params == None:
            setattr(object, 'depends_on', ['none'])
            setattr(object, 'dependent_offset', 0.0)
            solved_objects.append(object)
        elif "dependsOn" in params:
            setattr(object, 'depends_on', params['dependsOn'])
            setattr(object, 'dependent_offset', 0.0)
            if object.depends_on[0].lower() == 'none':
                solved_objects.append(object)
            else:
                unsolved_objects.append(object)
        else:
            setattr(object, 'depends_on', ['none'])
            setattr(object, 'dependent_offset', 0.0)
            solved_objects.append(object)
        _objects.remove(object)

    while len(unsolved_objects) > 0:
        res = solve_unsolved(solved_objects, unsolved_objects)
        solved_objects   = res[0]
        unsolved_objects = res[1]
        print "\n" + str(res)
    return solved_objects


def solve_unsolved(_solved, _unsolved):
    for unsol_obj in _unsolved:
        issue_max = 0
        for dependency in unsol_obj.depends_on:
            for sol_obj in _solved:
                print unsol_obj.depends_on, sol_obj.number
                if str(sol_obj.number) == dependency:
                    setattr(unsol_obj, 'dependent_offset', sol_obj.dependent_offset)
                    if hasattr(sol_obj, "estimate_value"):
                       ### issues
                       issue_max = max(issue_max, sol_obj.estimate_value)
                       # unsol_obj.dependent_offset += sol_obj.estimate_value
                    else:
                        ### milestones
                        milestone_max = 0.0
                        milestone_issues = gh.issues.list_by_repo(repoOwnerName, repoName, milestone=str(sol_obj.number)).all()
                        milestone_issues = calc_totals_for_issues(milestone_issues)
                        milestone_issues = calc_dependent_offsets(milestone_issues)
                        for iss in milestone_issues:
                            issue_duration = 0.0
                            if hasattr(iss, "estimate_value"):
                                issue_duration = float(iss.estimate_value)
                            issue_offset = 0.0
                            if hasattr(iss, "dependent_offset"):
                                issue_offset = float(iss.dependent_offset)
                            milestone_max = max(milestone_max, issue_duration + issue_offset)
                        unsol_obj.dependent_offset += milestone_max
                        
                    #break
        _solved.append(unsol_obj)
        _unsolved.remove(unsol_obj)
        unsol_obj.dependent_offset += issue_max
    return (_solved, _unsolved)


def quick_provide_estimate(_issues):
    _issues = calc_totals_for_issues(_issues)
    for issue in _issues:
        if hasattr(issue, "estimate_value") == False:
            valid_input_entered = False

            while not valid_input_entered:
                milestone = ""
                if hasattr(issue.milestone, "title"):
                    milestone = issue.milestone.title

                input = raw_input("Enter estimate for (" + milestone + ") " + issue.title + "(" + issue.body + ")")

                parsed_hours = extract_total_hour_month_day(input)[0]

                if parsed_hours > 0:
                    issue.body += "\n~estimate:" + input
                    data = dict(body=issue.body)
                    gh.issues.update(issue.number, data, user=repoOwnerName, repo=repoName)
                    valid_input_entered = True
                else:
                    print "Invalid input must be in the format 1w2d3h, 2d3h, 3h, 1w, etc"


def create_gantt_chart():
    ret = GANTT_BEGIN
    _milestones = gh.issues.milestones.list(user=repoOwnerName, repo=repoName).all()
    _milestones = calc_dependent_offsets(_milestones)
    _milestones.sort(key=lambda x: x.dependent_offset, reverse=False)

    for i in range(0, len(_milestones)):
        milestone_issues = gh.issues.list_by_repo(repoOwnerName, repoName, milestone=str(_milestones[i].number)).all()
        milestone_issues = calc_totals_for_issues(milestone_issues)
        milestone_total =  calc_work_in_milestone(milestone_issues)
        milestone_issues = calc_dependent_offsets(milestone_issues)
        duration = mult * float(milestone_total)/float(HOURS_IN_WORK_DAY)/float(DAYS_IN_WORK_WEEK)

        issue_max = 0.0
        for iss in milestone_issues:
            issue_duration = 0.0
            if hasattr(iss, "estimate_value"):
                issue_duration = mult * float(iss.estimate_value)/float(HOURS_IN_WORK_DAY)/float(DAYS_IN_WORK_WEEK)
            issue_offset = 0.0
            if hasattr(iss, "dependent_offset"):
                issue_offset = mult * float(iss.dependent_offset)/float(HOURS_IN_WORK_DAY)/float(DAYS_IN_WORK_WEEK)
            issue_max = max(issue_max, issue_duration + issue_offset)

        mile_offset = 0.0

        if hasattr(_milestones[i], "dependent_offset"):
            mile_offset = mult * float(_milestones[i].dependent_offset)/float(HOURS_IN_WORK_DAY)/float(DAYS_IN_WORK_WEEK)

        milestone_progress = 0
        if len(milestone_issues) > 0:
            milestone_progress = _milestones[i].closed_issues/len(milestone_issues)
        ret += "\\ganttgroup[progress=" + str(milestone_progress) + "]{" + str(i) + ". " + _milestones[i].title + "}{" + str(int(mile_offset + 1)) + "}{" + str(mile_offset + issue_max) + "}\\\\\n"

        milestone_issues.sort(key=lambda x: x.dependent_offset, reverse=False)

        for j in range(0, len(milestone_issues)):

            issue_duration = 0.0

            if hasattr(milestone_issues[j], "estimate_value"):
                issue_duration = mult * float(milestone_issues[j].estimate_value)/float(HOURS_IN_WORK_DAY)/float(DAYS_IN_WORK_WEEK)

            issue_offset = 0.0

            if hasattr(milestone_issues[j], "dependent_offset"):
                issue_offset = mult * float(milestone_issues[j].dependent_offset)/float(HOURS_IN_WORK_DAY)/float(DAYS_IN_WORK_WEEK)

            state = "0"
            if milestone_issues[j].state == "closed":
                state="100"

            ret += "\\ganttbar[progress=" + state + "]{" + str(i) + "." + str(j) + ". " + str(milestone_issues[j].title) + "}{" + str(int(issue_offset + mile_offset + 1)) + "}{" + str(int(mile_offset + issue_offset + issue_duration)) + "}\\\\\n"
    ret+="\\end{ganttchart}\n"
    ret+="\\end{document}"
    return ret

#issues_global = gh.issues.list_by_repo(SHS, repoName).all()

#quick_provide_estimate(gh.issues.list_by_repo(SHS, repoName).all())

print create_gantt_chart()
