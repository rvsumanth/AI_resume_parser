import sys
sys.path.insert(0, r"example_resumes\Sumanth-IBM-Resume.pdf")

from parser import parse_resume

result = parse_resume(r"example_resumes\Sumanth-IBM-Resume.pdf")   # or .docx
# print(result)