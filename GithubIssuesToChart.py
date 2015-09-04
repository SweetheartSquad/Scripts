__author__ = 'ryan'

from pygithub3 import Github
import sys

SHS = 'SweetheartSquad'

args = sys.argv

if len(args) > 3:

    repo     = args[1]
    username = args[2]
    password = args[3]

    out = '''\\documentclass{article}
    \\usepackage{tikz}
    \\usepackage[paperwidth=200in,paperheight=10in]{geometry}
    \\usetikzlibrary{arrows,shapes,positioning,trees}
    \\tikzset{
        basic/.style  = {draw, text width=2cm, font=\\sffamily, rectangle},
        root/.style   = {basic, rounded corners=2pt, thin, align=center, fill=green!30},
        level 1/.style={sibling distance=40mm},
        level 2/.style = {basic, rounded corners=6pt, thin, align=center, fill=green!60, text width=8em},
        level 3/.style = {basic, thin, align=left, fill=pink!60, text width=6.5em},
        edge from parent/.style={->, draw}
    }
    \\begin{document}
    \\begin{tikzpicture}
    % root of the the initial tree, level 1
    \\node[root] {''' + repo + '''}'''

    auth = dict(login=username, password=password)
    gh = Github(**auth)

    # Array of issues matched to the indexes of milestones
    milestone_issues_array = []

    milestones = gh.issues.milestones.list(user=SHS, repo=repo).all()

    # print out the milestones as first-level nodes
    for i in range(0, len(milestones)):
        out += '\nchild{node[level 2](c' + str(i) + ') {' + milestones[i].title + '}}'

    out += ''';
    \\newcounter{numMilestones}
    \\setcounter{numMilestones}{''' + str(len(milestones)-1) + '''}\n\n'''

    # for each milestone, print out the issues as second-level nodes
    out += '''\\begin{scope}[every node/.style={level 3}]\n'''
    for i in range(0, len(milestones)):
        issues = gh.issues.list_by_repo(SHS, repo, milestone=str(milestones[i].number)).all()

        milestone_issues_array.append(issues)
        for j in range(0, len(issues)):
            # The second level, relatively positioned nodes
            nodeNum = str(i)+str(j)
            if j == 0:
                nodeNumBelow = str(i)
            else:
                nodeNumBelow = str(i)+str(j-1)

            out += '''\\node [below of = c'''+nodeNumBelow+'''] (c'''+nodeNum+''') {''' + issues[j].title + '''};\n'''
        out += '''\\newcounter{numIssues''' + str(i) + '''}
    \\setcounter{numIssues''' + str(i) + '''}{''' + str(max(0,len(issues)-1)) + '''}\n\n'''

    out += '''\\end{scope}'''

    for i in range(0, len(milestones)):
        for j in range(0, len(milestone_issues_array[i])):
            out += '''\\draw[->] (c''' + str(i) + '''.195) |- (c''' + str(i) + str(j) + '''.west);\n'''
    out += '''\\end{tikzpicture}
    \\end{document}'''

    target = open(repo + "-Chart.tex", 'w')
    target.write(out)
    target.close()

else:
    print("Expected args Repository Name, Username, Password")