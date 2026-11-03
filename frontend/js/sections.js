/* sections.js
   Builds the new Academic navigation (Course > Semester > Subject > Syllabus/Notes/Questions/Quiz),
   the reusable Quiz, and the Library / PTU / CGC Landran sections.
   All text comes from the JSON files in /data (served by /api/academic/tree and /api/info/...), so to
   change content you edit the JSON, not this file. */

const NOT_AVAILABLE = 'Information not available yet. Please contact the college/help desk.';
let academicData = null;                                   // the whole academic.json
const acad = { course: null, semester: null, subject: null, view: 'syllabus' };   // what the student picked so far

const md = (text) => { try { return marked.parse(text || ''); } catch (e) { return escapeHtml(text); } };

// ---------------------------------------------------------------- loading
async function loadSections() {
  try {
    academicData = await (await fetch('/api/academic/tree')).json();
    renderAcademic();
    for (const [name, rootId] of [['library', 'library-root'], ['ptu', 'ptu-root'], ['cgc', 'cgc-root']]) {
      renderInfoSection(rootId, await (await fetch('/api/info/' + name)).json());
    }
  } catch (e) {
    const root = document.getElementById('academic-root');
    if (root) root.innerHTML = '<p class="text-slate-600">Could not load the data. Is the server running?</p>';
  }
  lucide.createIcons();
}
document.addEventListener('DOMContentLoaded', loadSections);

// ---------------------------------------------------------------- Academic navigation
function currentCourse() { return academicData.courses[acad.course]; }
function currentSemester() { return currentCourse().semesters[acad.semester]; }
function currentSubject() { return currentSemester().subjects[acad.subject]; }

// One click handler for every button: it reads data-course / data-sem / data-sub / data-view.
function acadSet(btn) {
  const d = btn.dataset;
  if ('course' in d) { acad.course = d.course || null; acad.semester = null; acad.subject = null; }
  if ('sem' in d) { acad.semester = d.sem || null; acad.subject = null; }
  if ('sub' in d) { acad.subject = d.sub === '' ? null : Number(d.sub); acad.view = 'syllabus'; }
  if ('view' in d) { acad.view = d.view; }
  renderAcademic();
}

// Used by the chat: "Open BCA Semester 5 in Academic"
function openAcademic(course, semester, subjectName, view) {
  if (!academicData || !academicData.courses[course]) return;
  acad.course = course; acad.semester = semester ? String(semester) : null; acad.subject = null; acad.view = view || 'syllabus';
  if (subjectName && acad.semester) {
    const i = currentSemester().subjects.findIndex(s => s.name === subjectName);
    acad.subject = i >= 0 ? i : null;
  }
  switchTab('academic'); renderAcademic();
}
function runChatAction(btn) { const a = JSON.parse(btn.dataset.action); openAcademic(a.course, a.semester, a.subject, a.view); }

function breadcrumb() {
  const crumbs = [`<button data-course="" onclick="acadSet(this)" class="text-blue-700 hover:underline">Academic</button>`];
  if (acad.course) crumbs.push(`<button data-sem="" onclick="acadSet(this)" class="text-blue-700 hover:underline">${escapeHtml(acad.course)}</button>`);
  if (acad.semester) crumbs.push(`<button data-sub="" onclick="acadSet(this)" class="text-blue-700 hover:underline">Semester ${escapeHtml(acad.semester)}</button>`);
  if (acad.subject !== null) crumbs.push(`<span class="font-semibold text-slate-800">${escapeHtml(currentSubject().name)}</span>`);
  return `<div class="text-sm text-slate-500 flex flex-wrap gap-2 items-center mb-4">${crumbs.join(' <span>›</span> ')}</div>`;
}

function renderAcademic() {
  const root = document.getElementById('academic-root');
  if (!root || !academicData) return;
  let html = `<h2 class="text-2xl font-extrabold text-slate-900 mb-1">📖 Academic</h2>` + breadcrumb();
  const card = 'text-left bg-slate-50 hover:bg-blue-50 border border-slate-200 hover:border-blue-400 rounded-xl p-4 transition';

  if (!acad.course) {                                                  // step 1: choose a course
    html += `<p class="text-slate-600 mb-3">Select your course</p><div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">` +
      Object.entries(academicData.courses).map(([key, c]) =>
        `<button data-course="${escapeHtml(key)}" onclick="acadSet(this)" class="${card}"><div class="text-lg font-bold">🎓 ${escapeHtml(key)}</div><div class="text-xs text-slate-500">${escapeHtml(c.full_name || '')}</div></button>`).join('') + `</div>`;
  } else if (!acad.semester) {                                          // step 2: choose a semester (each course has its own count)
    html += `<p class="text-slate-600 mb-3">${escapeHtml(currentCourse().full_name || acad.course)}: select a semester</p><div class="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-6 gap-3">` +
      Object.entries(currentCourse().semesters).map(([n, s]) =>
        `<button data-sem="${n}" onclick="acadSet(this)" class="${card}"><div class="font-bold">Semester ${n}</div><div class="text-xs text-slate-500">${s.subjects.length ? s.subjects.length + ' subjects' : 'no subjects yet'}</div></button>`).join('') + `</div>` + schemesHtml(currentCourse());
  } else if (acad.subject === null) {                                   // step 3: choose a subject
    const sem = currentSemester();
    html += `<p class="text-slate-600 mb-3">${escapeHtml(acad.course)} Semester ${acad.semester}: select a subject</p>`;
    if (sem.note) html += `<div class="bg-amber-50 border border-amber-200 text-amber-900 text-sm rounded-lg p-3 mb-3">${escapeHtml(sem.note)}</div>`;
    html += sem.subjects.length ? `<div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">` + sem.subjects.map((s, i) => {
      const has = (v, label) => `<span class="${v.length ? 'text-emerald-700' : 'text-slate-400'}">${v.length ? '✓' : '–'} ${label}</span>`;
      return `<button data-sub="${i}" onclick="acadSet(this)" class="${card}"><div class="font-semibold">${escapeHtml(s.name)}</div>` +
        `<div class="text-xs text-slate-500 mb-1">${escapeHtml(s.code || '')}</div><div class="text-xs flex flex-wrap gap-x-3">${has(s.syllabus, 'Syllabus')}${has(s.notes, 'Notes')}${has(s.important_questions, 'Questions')}${has(s.quiz, 'Quiz')}</div></button>`;
    }).join('') + `</div>` : `<div class="bg-slate-50 border border-slate-200 rounded-lg p-4 text-slate-600">${NOT_AVAILABLE}</div>`;
  } else {                                                              // step 4: syllabus / notes / questions / quiz
    const tabs = [['syllabus', 'Syllabus'], ['notes', 'Notes'], ['important_questions', 'Important Questions'], ['quiz', 'Quiz']];
    html += `<div class="flex flex-wrap gap-2 mb-4">` + tabs.map(([v, label]) =>
      `<button data-view="${v}" onclick="acadSet(this)" class="px-4 py-2 rounded-lg text-sm font-semibold border ${acad.view === v ? 'bg-blue-700 text-white border-blue-700' : 'bg-white text-slate-700 border-slate-300 hover:border-blue-400'}">${label}</button>`).join('') + `</div><div id="acad-content"></div>`;
  }
  root.innerHTML = html;
  if (acad.subject !== null) renderSubjectContent(document.getElementById('acad-content'));
}

// Batch years PTU has published for this course (from ptu.ac.in/syllabus; stored in academic.json as ptu_schemes)
function schemesHtml(course) {
  if (!course.ptu_schemes || !course.ptu_schemes.length) return '';
  return `<div class="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm"><div class="font-semibold text-blue-900 mb-1">PTU syllabus batches (official, ptu.ac.in/syllabus)</div>` +
    `<ul class="list-disc ml-5 text-slate-700">${course.ptu_schemes.map(p => `<li><b>${escapeHtml(p.programme)}:</b> ${escapeHtml(p.batches)}</li>`).join('')}</ul>` +
    `<p class="text-xs text-slate-600 mt-1">Choose the batch for your admission year on the <a class="text-blue-700 underline" target="_blank" href="https://ptu.ac.in/syllabus">PTU syllabus page</a>.</p></div>`;
}

const emptyBox = () => `<div class="bg-slate-50 border border-slate-200 rounded-lg p-4 text-slate-600">${NOT_AVAILABLE}</div>`;

function renderSubjectContent(box) {
  const s = currentSubject();
  if (acad.view === 'syllabus') {
    const course = currentCourse();
    const portal = `<a class="text-blue-700 underline" target="_blank" href="https://ptu.ac.in/syllabus">PTU syllabus portal</a>`;
    box.innerHTML = !s.syllabus.length ? emptyBox() + (course.overview ? `<p class="text-sm text-slate-600 mt-3">${escapeHtml(course.overview)}</p>` : '') +
      schemesHtml(course) + `<p class="text-sm text-slate-600 mt-2">The official syllabus is on the ${portal}: choose your programme and the batch for your admission year.</p>` : s.syllabus.length ? s.syllabus.map(u => `<div class="border-l-4 border-blue-600 pl-3 mb-3"><div class="font-bold">${escapeHtml(u.unit)}</div><div class="text-slate-700">${escapeHtml(u.topics)}</div></div>`).join('') +
      `<p class="text-xs text-slate-500">${escapeHtml(s.syllabus_note || '')} Source: project data, please verify on the <a class="text-blue-700 underline" target="_blank" href="https://ptu.ac.in/syllabus">PTU syllabus portal</a>.</p>` : emptyBox();
  } else if (acad.view === 'notes') {
    box.innerHTML = s.notes.length ? `<p class="text-xs text-slate-500 mb-3">Study notes for revision. Not official university material.</p>` + s.notes.map(n =>
      `<div class="border border-slate-200 rounded-xl p-4 mb-4"><h4 class="font-bold text-lg">${escapeHtml(n.unit)}: ${escapeHtml(n.title)}</h4><p class="text-slate-700 mt-1">${escapeHtml(n.explanation)}</p>` +
      (n.definitions && n.definitions.length ? `<h5 class="font-semibold mt-3">Important definitions</h5><ul class="list-disc ml-5 text-slate-700">${n.definitions.map(d => `<li><b>${escapeHtml(d[0])}:</b> ${escapeHtml(d[1])}</li>`).join('')}</ul>` : '') +
      (n.example ? `<h5 class="font-semibold mt-3">Example</h5><pre class="bg-slate-900 text-slate-100 text-xs rounded-lg p-3 overflow-x-auto">${escapeHtml(n.example)}</pre>` : '') +
      (n.exam_points && n.exam_points.length ? `<h5 class="font-semibold mt-3">Exam points</h5><ul class="list-disc ml-5 text-slate-700">${n.exam_points.map(p => `<li>${escapeHtml(p)}</li>`).join('')}</ul>` : '') + `</div>`).join('') : emptyBox();
  } else if (acad.view === 'important_questions') {
    box.innerHTML = s.important_questions.length ? s.important_questions.map(g => `<h4 class="font-bold mt-3">${escapeHtml(g.unit)}</h4><ol class="list-decimal ml-5 text-slate-700">${g.questions.map(q => `<li>${escapeHtml(q)}</li>`).join('')}</ol>`).join('') +
      `<p class="text-xs text-slate-500 mt-3">${escapeHtml(s.questions_note || '')}</p>` : emptyBox();
  } else {
    if (s.quiz.length) renderQuiz(box, s.quiz); else box.innerHTML = emptyBox();
  }
}

// ---------------------------------------------------------------- reusable Quiz (same code for every course and subject)
// questions = [{question, options:[4 texts], answer: index of the correct option, explanation}]
function renderQuiz(box, questions) {
  let index = 0, score = 0;
  function show() {
    if (index >= questions.length) {                                    // finished: final score + restart
      box.innerHTML = `<div class="text-center p-6 bg-blue-50 rounded-xl"><div class="text-2xl font-extrabold">Your Score: ${score}/${questions.length}</div>` +
        `<button id="quiz-restart" class="mt-4 bg-blue-700 text-white font-semibold px-5 py-2 rounded-lg">Restart quiz</button></div>`;
      box.querySelector('#quiz-restart').onclick = () => { index = 0; score = 0; show(); };
      return;
    }
    const q = questions[index];
    box.innerHTML = `<div class="text-xs text-slate-500 mb-1">Question ${index + 1} of ${questions.length} · Score: ${score}</div><div class="font-semibold mb-3">${escapeHtml(q.question)}</div>` +
      q.options.map((o, i) => `<button data-i="${i}" class="quiz-opt block w-full text-left border border-slate-300 rounded-lg px-3 py-2 mb-2 hover:border-blue-400"><b>${'ABCD'[i]}.</b> ${escapeHtml(o)}</button>`).join('') + `<div id="quiz-feedback"></div>`;
    box.querySelectorAll('.quiz-opt').forEach(btn => btn.onclick = () => {
      const chosen = Number(btn.dataset.i);
      if (chosen === q.answer) score++;
      box.querySelectorAll('.quiz-opt').forEach(b => {                  // lock the answers and colour them
        b.disabled = true;
        if (Number(b.dataset.i) === q.answer) b.classList.add('bg-emerald-100', 'border-emerald-500');
        else if (b === btn) b.classList.add('bg-red-100', 'border-red-400');
      });
      box.querySelector('#quiz-feedback').innerHTML = `<p class="text-sm text-slate-600 my-2">${chosen === q.answer ? '✅ Correct.' : '❌ Not quite.'} ${escapeHtml(q.explanation || '')}</p>` +
        `<button id="quiz-next" class="bg-blue-700 text-white font-semibold px-4 py-2 rounded-lg">${index + 1 < questions.length ? 'Next question' : 'See my score'}</button>`;
      box.querySelector('#quiz-next').onclick = () => { index++; show(); };
    });
  }
  show();
}

// ---------------------------------------------------------------- Library / PTU / CGC Landran sections (topic cards)
function renderInfoSection(rootId, data) {
  const root = document.getElementById(rootId);
  if (!root) return;
  const cards = data.topics.map(t => {
    const body = (t.answer ? `<div class="prose prose-sm max-w-none text-slate-700">${md(t.answer)}</div>` : '') +
      (t.unconfirmed ? `<div class="mt-2 bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm"><div class="text-xs font-bold text-amber-800 mb-1">From the project's stored data, not confirmed against the official website</div><div class="prose prose-sm max-w-none text-slate-700">${md(t.unconfirmed)}</div></div>` : '') +
      (!t.answer && !t.unconfirmed ? `<p class="text-slate-500 text-sm">${NOT_AVAILABLE}</p>` : '');
    const links = (t.links || []).map(l => `<a href="${l.url}" target="_blank" rel="noopener" class="badge-source"><span>${escapeHtml(l.title)}</span></a>`).join(' ');
    return `<div class="bg-white border border-slate-200 rounded-xl p-5 shadow-sm"><h3 class="font-bold text-slate-900 mb-2">${escapeHtml(t.title)}</h3>${body}` +
      `<div class="mt-3 flex flex-wrap gap-2 items-center">${links}<button onclick="switchTab('chat'); preprompt('${escapeHtml(t.title).replace(/'/g, '')}')" class="text-xs text-blue-700 font-semibold hover:underline">Ask the chatbot →</button></div></div>`;
  }).join('');
  root.innerHTML = `<div class="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm mb-6"><h2 class="text-2xl font-extrabold text-slate-900">${data.icon} ${escapeHtml(data.title)}</h2>` +
    `<p class="text-slate-600 mt-1 text-sm">${escapeHtml(data.intro || '')}</p></div><div class="grid md:grid-cols-2 gap-4">${cards}</div>`;
}
