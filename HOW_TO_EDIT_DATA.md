# How to add or edit content (no code changes needed)

All content lives in the `data/` folder. The server reads these files on every question, so after you save a file you can
just ask the chatbot again (refresh the website to see the new Academic cards).
After editing, run `python -m pytest -q`: two tests check your files for mistakes (wrong quiz format, duplicate ids...).

| File | What it holds |
|---|---|
| `data/academic.json` | Courses > Semesters > Subjects > syllabus / notes / important_questions / quiz |
| `data/library.json` | Library topics (location, timing, rules, issue, return, limit, facilities, digital, search, contact) |
| `data/ptu.json` | PTU topics (about, academic system, syllabus, examination, results, regulations...) |
| `data/cgc_landran.json` | CGC Landran topics (about, campus, departments, admission, facilities, clubs, sports, placements, contact...) |

## Add a new course (example: B.Com)
In `academic.json`, inside `"courses"`, add (the number of semesters is up to you):
```json
"B.Com": {
  "full_name": "Bachelor of Commerce",
  "aliases": ["bcom", "commerce"],
  "semesters": { "1": {"subjects": []}, "2": {"subjects": []}, "3": {"subjects": []},
                 "4": {"subjects": []}, "5": {"subjects": []}, "6": {"subjects": []} }
}
```
`aliases` are other ways students may write the course (lower case, no dots). The course now appears on the Academic page
and the chatbot understands "B.Com semester 2 notes".

## Add a new semester
Inside the course's `"semesters"`, add `"7": {"subjects": []}`. Optional: `"note": "text shown above the subject list"`.

## Add a new subject
Inside a semester's `"subjects"` list add (empty lists simply show "Information not available yet"):
```json
{ "name": "Financial Accounting", "code": "BC101", "aliases": ["accounting"],
  "syllabus": [], "notes": [], "important_questions": [], "quiz": [] }
```
`aliases` are short names students might type ("accounting notes").

## Add syllabus, notes, important questions, quiz to a subject
```json
"syllabus": [ {"unit": "Unit I", "topics": "Topics of unit one"} ],
"notes": [ { "unit": "Unit I", "title": "Topic name", "explanation": "Simple explanation.",
             "definitions": [["Term", "Meaning"]], "example": "optional example text",
             "exam_points": ["Point 1", "Point 2"] } ],
"important_questions": [ {"unit": "Unit I", "questions": ["Question 1", "Question 2"]} ],
"quiz": [ { "question": "What does HTML stand for?",
            "options": ["Hyper Text Markup Language", "High Text Machine Language", "Hyperlink Text Management Language", "Home Tool Markup Language"],
            "answer": 0, "explanation": "Optional reason." } ]
```
`answer` is the position of the correct option: 0 = A, 1 = B, 2 = C, 3 = D. A quiz question must have exactly 4 options.

## Add or change a library / PTU / CGC topic
Each topic in the three topic files looks like this:
```json
{ "id": "timing", "title": "Library timings",
  "keywords": ["timing", "timings", "hours", "opening"],
  "answer": "Text that is confirmed (official).",
  "unconfirmed": "Text from older stored data. It is shown with a 'not confirmed' warning.",
  "links": [ {"title": "Library Rules (PDF)", "url": "https://..."} ] }
```
- Put checked facts in `answer`. If you are not sure a fact is correct, put it in `unconfirmed`.
- Leave both as `null` to show "Information not available yet".
- `keywords` decide which topic wins: the topic with the most matching words wins, and a longer phrase scores more.
  To make a new question type work, add its words to that topic (e.g. add "closing time" to timing).
- Every topic needs a unique `id`. Add a whole new topic by copying one block and changing the id, title and keywords.

## Courses, fees, eligibility and duration (`data/cgc_programmes.json` and `data/course_info.json`)
Both files use the same layout: **categories**, and inside each category a list of **courses**.
To add a course, copy one course block inside the right category and change the values:
```json
{
  "name": "BCA — Bachelor of Computer Applications",
  "level": "Undergraduate",
  "cgc_url": "https://www.cgc.edu.in/bca",
  "duration": "3 Years",
  "eligibility": "10+2 with minimum 50% marks",
  "fee": "Approx Rs ... (confirm officially)",
  "aliases": ["bca"]
}
```
- `data/cgc_programmes.json` feeds the **Courses page** and the chatbot's "tell me about <course>" answers.
- `data/course_info.json` feeds the chatbot's **fees / eligibility / duration** answers.
- Both files currently hold the same list. When you change a course, change it in both files.
- If you do not know a value, leave that key out. The app then shows "Information not available yet".
- `aliases` are the words students may type (lower case, no dots). Do not use very short words like "it" or "me".
- A course with `"cgc_url": null` is shown on the Courses page but is not matched by the chatbot.

## PTU syllabus batches (`data/ptu_syllabus_index.json`)
Same layout (categories > courses). Each course has `name`, `aliases` and `years`.
Optional: add `"batches": "2021, 2025"` to a course to show its PTU syllabus batches (copy them from https://ptu.ac.in/syllabus).
Without `batches` the app says "Information not available yet".
