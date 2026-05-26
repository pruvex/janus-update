import json
import sys
import re

# Read the decision report
with open('decision_report.json', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()
    
# Remove all control characters except newline and tab
content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', content)

# Parse JSON
data = json.loads(content)

# Extract the markdown report from the 'report' key
markdown_report = data.get('report', '')
print(markdown_report)
print('\n\n---\n\n')

# Check problem_profiles for the 5 core skills
problem_profiles = data.get('problem_profiles', {})
core_skills = ['system.weather', 'filesystem.list_directory', 'knowledge.query', 'system.local_business', 'calendar.list_events']

print('# Core Skills Problem Profiles\n')
for skill in core_skills:
    if skill in problem_profiles:
        profile = problem_profiles[skill]
        print(f'## {skill}')
        print(f'- {profile}')
    else:
        print(f'## {skill}')
        print('- No problem profile found')
    print()
