__author__ = 'ryan'

from pygithub3 import Github
import sys


# currently just escapes the percent sign
# would need to be updated to include a lot more for serious use,
# but this covers this %20 = space url issue
def latexEncode(str):
    str = str.replace("%", "\%")
    return str


SHS = 'SweetheartSquad'

args = sys.argv

if len(args) < 3:
    sys.exit("Expected args Repository Name, Username, Password")

repoName = args[1]
username = args[2]
password = args[3]

out = '''\\documentclass{article}
\\newcommand{\\boxSize}{12em}

\\usepackage{tikz}
\\usepackage{hyperref}
\\usepackage[
paperwidth=100in,paperheight=10in, %pagesize
top=0pt, right=0pt, left=0pt, bottom=0pt %margins
]{geometry}
\\usetikzlibrary{arrows,shapes,positioning,trees}
\\tikzset{
basic/.style   = {draw, text width=\\boxSize, font=\\sffamily, rectangle},
root/.style    = {basic, thin, align=center, fill=green!30},
level 1/.style = {sibling distance=\\boxSize+1em},
level 2/.style = {basic, thin, align=center, fill=green!60, text width=\\boxSize},
level 3/.style = {basic, thin, align=left, fill=pink!60, text width=\\boxSize-1em},
edge from parent/.style={draw, edge from parent path={(\\tikzparentnode.south) -- +(0,-8pt) -| (\\tikzchildnode)}}
}'''

auth = dict(login=username, password=password)
gh = Github(**auth)

# Array of issues matched to the indexes of milestones
milestone_issues_array = []


milestones = gh.issues.milestones.list(user=SHS, repo=repoName).all()
repo = gh.repos.get(user=SHS, repo=repoName)

# Start the tree
out += '''
\\begin{document}
\\begin{tikzpicture}
\\node[root] {\href{'''+repo.html_url+'''}{''' + repoName + '''}}'''

# print out the milestones as first-level nodes
for i in range(0, len(milestones)):
    out += '\nchild{node[level 2](c' + str(i) + ') {\href{' + latexEncode(milestones[i].html_url) + '}{' + str(i)+". " + latexEncode(milestones[i].title) + '}}}'

out += ''';
\\newcounter{numMilestones}
\\setcounter{numMilestones}{''' + str(len(milestones)-1) + '''}\n\n'''

# for each milestone, print out the issues as second-level nodes
out += '''\\begin{scope}[every node/.style={level 3}]\n'''
for i in range(0, len(milestones)):
    issues = gh.issues.list_by_repo(SHS, repoName, milestone=str(milestones[i].number)).all()

    milestone_issues_array.append(issues)
    for j in range(0, len(issues)):
        # The second level, relatively positioned nodes
        nodeNum = str(i)+"_"+str(j)
        if j == 0:
            nodeNumBelow = str(i)
        else:
            nodeNumBelow = str(i)+"_"+str(j-1)

        out += '''\\node [below of = c'''+nodeNumBelow+'''] (c'''+nodeNum+''') {\href{'''+latexEncode(issues[j].html_url)+'''}{''' +str(i)+"."+str(j)+". " + latexEncode(issues[j].title) + '''}};\n'''
    out += '''\\newcounter{numIssues''' + str(i) + '''}
\\setcounter{numIssues''' + str(i) + '''}{''' + str(max(0,len(issues)-1)) + '''}\n\n'''

out += '''\\end{scope}'''

for i in range(0, len(milestones)):
    for j in range(0, len(milestone_issues_array[i])):
        out += '''\\draw[-] (c''' + str(i) + '''.west) |- (c''' + str(i) +"_"+ str(j) + '''.west);\n'''
out += '''\\end{tikzpicture}
\\end{document}'''

target = open(repoName + "-Chart.tex", 'w')
target.write(out)
target.close()