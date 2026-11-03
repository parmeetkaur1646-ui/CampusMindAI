# What changed (fix for repeated/wrong answers)

**Cause:** any question that matched no keyword fell back to the same "CGC Landran Highlights" answer, and fees, scholarships,
placements and contacts had no handling. Syllabus, notes and quiz were hard-coded for BCA Sem 5 / PHP.

**Now**
- `backend/official_data.py`: facts copied from cgc.edu.in (programme list with page links, helplines, address, library page,
  admissions steps). If the site doesn't publish something (e.g. fee amounts) it is not in the file.
- `backend/official_answers.py`: separate answer for each question type, for every CGC programme. Unknown questions get an honest
  "can't answer reliably" message instead of a generic answer.
- Syllabus: PTU's syllabus page blocks automated reading, so the app points to the official PTU portal and programme page for any
  programme and semester instead of listing subjects it can't verify.
- Notes and quizzes for ANY subject need an AI key: set `OPENAI_API_KEY` (and `AI_API_BASE`/`AI_MODEL` for another provider).
  Without a key only the curated PHP and Cloud quizzes work, and the app says so.
- Library page, hours, loan limits, fines, DELNET/NDLI/IEEE and the 40,000-volume claim were not on the official page and were removed.
  Placement numbers now match the CGC site.

Re-check `official_data.py` against cgc.edu.in from time to time. Do not zip `.venv` or `.git` when sharing the project.

---
# Update 2: question matching, Academic system, and CGC / PTU / Library sections

- `backend/chat_engine.py` (new, simple keyword scoring) understands Library, PTU, CGC Landran and Academic questions before the older
  code runs. Library questions are split into location / timing / open-now / rules / issue / return / limit / facilities / digital / search / contact.
- Academic is fully data-driven: `data/academic.json` holds Course > Semester > Subject > syllabus / notes / important_questions / quiz.
  Each course has its own semesters and subjects. One quiz function serves every course.
- Library, PTU and CGC Landran topics live in `data/library.json`, `data/ptu.json`, `data/cgc_landran.json`.
  Facts confirmed on cgc.edu.in are in `answer`; older project data that could not be confirmed is shown separately as "not confirmed".
- New files: `backend/chat_engine.py`, `backend/routes/info.py`, `frontend/js/sections.js`, `data/*.json`, `HOW_TO_EDIT_DATA.md`,
  `tests/test_chat_engine.py`.
- Changed files: `backend/routes/chat.py` (calls the engine, returns `actions`), `backend/main.py` (registers info routes),
  `backend/official_answers.py` (fallback wording), `frontend/index.html` (new sections, PTU tab, existing content kept inside "More" boxes),
  `frontend/js/app.js` (PTU tab, chat action buttons), tests.

---
# Update 3: help-desk data, honest badge, formatting

- Data from the supplied help-desk code was added: fees/eligibility/duration (`data/course_info.json`), faculty, library figures, hostel, CCT placements,
  contact details. It is shown as "not confirmed" because it is not listed on the official CGC pages. Where two stored sources disagree
  (library borrowing rule 21 days vs 14 days) both are shown.
- The "CGC Verified" badge was hard-coded. It is now green only for answers confirmed on the official site, amber ("Please confirm officially")
  for stored project data, and absent for "I could not find" answers.
- Lists in answers now show one item per line. Subject names ending in "C++" are matched. "eligibility?" after "bca fees" remembers the course.

---
# Update 4: PTU syllabus page and official library rules

- Syllabus links now point to https://ptu.ac.in/syllabus. The page lists, for every programme, the batch years (schemes) PTU has published; these are stored in
  `data/ptu_syllabus_index.json` and shown in the Academic page, in chatbot syllabus answers, and for "which syllabus schemes does PTU have for MCA?".
  The page does not expose the individual PDF links, so students open the page and pick their batch.
- Library rules, borrowing limit, issue and return answers now come from the official CGC Library Rules PDF (3 books for 21 days for graduate and postgraduate
  students, card rules, belongings, conduct, lost books). The older "14 days / 5 books for PG" data was wrong and is removed. Timings and exact location stay "not confirmed".

---
# Update 5: programme list as data
- New `data/cgc_programmes.json` (41 programmes in 6 groups, with CGC links and PTU batches). `backend/official_data.py` and `backend/routes/courses.py` read it,
  so the old hardcoded Courses list (with unconfirmed eligibility/"features" text) is gone. Details we do not have show "Information not available yet".
- "tell me about MBA digital marketing" now answers about the programme instead of about CGC.
