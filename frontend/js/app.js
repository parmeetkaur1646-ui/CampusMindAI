if (window.marked) marked.setOptions({ breaks: true });   // a single new line in an answer becomes a line break
// CampusMind AI - Application Controller
let currentSessionId = localStorage.getItem('campusmind_session_id') || ('session-' + Math.random().toString(36).substring(2, 10));
localStorage.setItem('campusmind_session_id', currentSessionId);

let currentMode = 'Student';
let adminToken = localStorage.getItem('campusmind_admin_token') || null;

// Initialize on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  lucide.createIcons();
  fetchContextMemory();
  loadAcademicSyllabus();
  loadLibraryResources('all');
  loadCourses();
  
  if (adminToken) {
    showAdminPanel();
  }
});

// Navigation Tab Switcher
function switchTab(tab) {
  const tabs = ['home', 'chat', 'academic', 'library', 'courses', 'college', 'ptu', 'admin'];
  tabs.forEach(t => {
    const el = document.getElementById(`view-${t}`);
    const btn = document.getElementById(`tab-${t}`);
    if (el) el.classList.add('hidden');
    if (btn) btn.classList.remove('active', 'border-b-2', 'border-blue-700', 'text-blue-700');
  });

  const activeEl = document.getElementById(`view-${tab}`);
  const activeBtn = document.getElementById(`tab-${tab}`);
  if (activeEl) activeEl.classList.remove('hidden');
  if (activeBtn) activeBtn.classList.add('active', 'border-b-2', 'border-blue-700', 'text-blue-700');

  // Close mobile menu if open
  const mob = document.getElementById('mobile-menu');
  if (mob && !mob.classList.contains('hidden')) {
    mob.classList.add('hidden');
  }

  lucide.createIcons();
}

function toggleMobileMenu() {
  const mob = document.getElementById('mobile-menu');
  if (mob) mob.classList.toggle('hidden');
}

// Student Journey Modes
function setJourneyMode(mode) {
  currentMode = mode;
  ['Student', 'Applicant', 'Faculty', 'Guest'].forEach(m => {
    const btn = document.getElementById(`mode-${m}`);
    if (btn) {
      if (m === mode) {
        btn.classList.add('active', 'bg-blue-900', 'text-white');
        btn.classList.remove('text-slate-600');
      } else {
        btn.classList.remove('active', 'bg-blue-900', 'text-white');
        btn.classList.add('text-slate-600');
      }
    }
  });

  // Update memory on backend
  fetch('/api/chat/memory/update', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: currentSessionId, mode: mode })
  }).then(r => r.json()).then(data => {
    renderMemoryBadge(data.memory);
  }).catch(console.error);
}

// Fetch Context Memory
async function fetchContextMemory() {
  try {
    const res = await fetch(`/api/chat/memory/${currentSessionId}`);
    if (res.ok) {
      const data = await res.json();
      renderMemoryBadge(data.memory);
    }
  } catch (err) {
    console.error('Error fetching context memory:', err);
  }
}

function renderMemoryBadge(memory) {
  const display = document.getElementById('memory-display');
  if (!display) return;
  const course = memory?.course || 'None';
  const sem = memory?.semester ? `Sem ${memory.semester}` : 'None';
  const subj = memory?.subject ? ` • ${memory.subject}` : '';
  display.textContent = `Course: ${course} • ${sem}${subj}`;
}

// Clear Context Memory
async function clearContextMemory() {
  try {
    const res = await fetch('/api/chat/memory/clear', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: currentSessionId })
    });
    if (res.ok) {
      renderMemoryBadge({ course: null, semester: null, subject: null });
      appendBotMessage("Conversation memory cleared. What would you like to explore next?");
    }
  } catch (err) {
    console.error(err);
  }
}

// Edit Memory Modal
function openEditMemoryModal() {
  document.getElementById('modal-edit-memory').classList.remove('hidden');
  lucide.createIcons();
}
function closeEditMemoryModal() {
  document.getElementById('modal-edit-memory').classList.add('hidden');
}
async function saveContextMemory() {
  const course = document.getElementById('modal-course').value.trim() || null;
  const sem = document.getElementById('modal-sem').value.trim() || null;
  const subj = document.getElementById('modal-subject').value.trim() || null;

  try {
    const res = await fetch('/api/chat/memory/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: currentSessionId,
        course: course,
        semester: sem,
        subject: subj,
        mode: currentMode
      })
    });
    if (res.ok) {
      const data = await res.json();
      renderMemoryBadge(data.memory);
      closeEditMemoryModal();
    }
  } catch (err) {
    console.error(err);
  }
}

// Preprompt from Landing page
function preprompt(query) {
  const input = document.getElementById('chat-input');
  if (input) {
    input.value = query;
    handleChatSubmit(new Event('submit'));
  }
}

function sendQuickPrompt(query) {
  const input = document.getElementById('chat-input');
  if (input) {
    input.value = query;
    handleChatSubmit(new Event('submit'));
  }
}

// Chat Submission
async function handleChatSubmit(e) {
  if (e && e.preventDefault) e.preventDefault();
  const input = document.getElementById('chat-input');
  const query = input.value.trim();
  if (!query) return;

  // Append user message
  appendUserMessage(query);
  input.value = '';

  // Append thinking bubble
  const thinkingId = 'thinking-' + Date.now();
  appendThinkingBubble(thinkingId);

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: currentSessionId,
        message: query,
        mode: currentMode
      })
    });

    removeThinkingBubble(thinkingId);

    if (res.ok) {
      const data = await res.json();
      appendBotMessage(data.message, data.sources, data.follow_up_suggestions, data.intent, data.actions, data.verification);
      if (data.memory) {
        renderMemoryBadge(data.memory);
      }
      updateQuickPromptsBar(data.follow_up_suggestions);
    } else {
      console.error('Chat request failed with status', res.status);   // look at the terminal running run.py for the details
      appendBotMessage("I encountered an issue processing that query. Please try again or visit the official CGC Landran portal.");
    }
  } catch (err) {
    removeThinkingBubble(thinkingId);
    appendBotMessage("Connection error. Ensure the CampusMind AI backend server is running.");
    console.error(err);
  }
}

function appendUserMessage(text) {
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'flex justify-end gap-3';
  div.innerHTML = `
    <div class="chat-msg-user px-4 py-3 max-w-xl text-sm leading-relaxed shadow-sm">
      ${escapeHtml(text)}
    </div>
  `;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function appendThinkingBubble(id) {
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.id = id;
  div.className = 'flex gap-3';
  div.innerHTML = `
    <div class="w-9 h-9 rounded-full bg-blue-700 flex items-center justify-center text-white flex-shrink-0 shadow-sm">
      <i data-lucide="bot" class="w-5 h-5"></i>
    </div>
    <div class="chat-msg-bot p-4 max-w-xl flex items-center gap-2 text-xs text-slate-500">
      <span class="ai-orb"></span> Searching CGC knowledge base & synthesizing response...
    </div>
  `;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  lucide.createIcons();
}

function removeThinkingBubble(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function appendBotMessage(markdownText, sources = [], followUps = [], intent = '', actions = [], verification = 'none') {
  // Badge: green only when the answer is confirmed on the official site; amber when it comes from stored project data.
  const badgeHtml = verification === 'verified'
    ? '<span class="badge-verified"><i data-lucide="check-circle" class="w-3 h-3"></i> CGC Verified</span>'
    : verification === 'unconfirmed'
      ? '<span class="text-xs font-semibold text-amber-800 bg-amber-100 border border-amber-300 rounded-full px-2 py-0.5">Please confirm officially</span>' : '';
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'flex gap-3';

  // Render markdown with marked.js
  let parsedHtml = '';
  try {
    parsedHtml = marked.parse(markdownText);
  } catch (e) {
    parsedHtml = escapeHtml(markdownText).replace(/\n/g, '<br>');
  }

  // Source badges
  let sourcesHtml = '';
  if (sources && sources.length > 0) {
    sourcesHtml = `
      <div class="mt-3 pt-3 border-t border-slate-100">
        <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">Official Sources:</span>
        <div class="flex flex-wrap gap-1.5">
          ${sources.map(s => `
            <a href="${s.url}" target="_blank" class="badge-source">
              <i data-lucide="link-2" class="w-3 h-3"></i>
              <span>${s.title || 'Official Portal'}</span>
            </a>
          `).join('')}
        </div>
      </div>
    `;
  }

  // Buttons such as "Open BCA Semester 5 in Academic" (see sections.js)
  const actionsHtml = (actions && actions.length) ? `<div class="flex flex-wrap gap-2 pt-2">${actions.map(a =>
    `<button class="bg-blue-700 text-white text-xs font-semibold px-3 py-2 rounded-lg" data-action="${escapeHtml(JSON.stringify(a))}" onclick="runChatAction(this)">${escapeHtml(a.label)}</button>`).join('')}</div>` : '';

  const msgId = 'msg-' + Date.now();

  div.innerHTML = `
    <div class="w-9 h-9 rounded-full bg-blue-700 flex items-center justify-center text-white flex-shrink-0 shadow-sm">
      <i data-lucide="bot" class="w-5 h-5"></i>
    </div>
    <div class="chat-msg-bot p-5 max-w-2xl space-y-2 shadow-sm text-sm">
      <div class="flex items-center justify-between text-xs pb-1 border-b border-slate-100">
        <span class="font-bold text-blue-900">CampusMind AI</span>
        ${badgeHtml}
      </div>
      
      <div class="prose prose-sm max-w-none text-slate-800 leading-relaxed">
        ${parsedHtml}
      </div>

      ${actionsHtml}
      ${sourcesHtml}

      <!-- Message Actions: Copy & Feedback -->
      <div class="flex items-center justify-between pt-2 border-t border-slate-100 text-xs text-slate-400">
        <button onclick="copyMessageText('${msgId}')" class="hover:text-blue-600 flex items-center gap-1 transition">
          <i data-lucide="copy" class="w-3.5 h-3.5"></i> Copy
        </button>
        <div class="flex items-center gap-2">
          <span>Was this helpful?</span>
          <button onclick="submitMessageFeedback('${msgId}', 'helpful')" title="Helpful" class="hover:text-emerald-600"><i data-lucide="thumbs-up" class="w-3.5 h-3.5"></i></button>
          <button onclick="submitMessageFeedback('${msgId}', 'not_helpful')" title="Not Helpful" class="hover:text-rose-600"><i data-lucide="thumbs-down" class="w-3.5 h-3.5"></i></button>
        </div>
      </div>
      <div id="${msgId}" class="hidden">${escapeHtml(markdownText)}</div>
    </div>
  `;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  lucide.createIcons();
}

function updateQuickPromptsBar(suggestions) {
  const bar = document.getElementById('quick-prompts-bar');
  if (!bar || !suggestions || suggestions.length === 0) return;
  bar.innerHTML = `
    <span class="text-slate-400 font-semibold uppercase text-[10px]">Follow up:</span>
    ${suggestions.map(s => `
      <button onclick="sendQuickPrompt('${escapeHtml(s)}')" class="bg-white border border-slate-200 hover:border-blue-400 px-2.5 py-1 rounded-full text-slate-700 transition">
        ${escapeHtml(s)}
      </button>
    `).join('')}
  `;
}

function copyMessageText(id) {
  const el = document.getElementById(id);
  if (el) {
    navigator.clipboard.writeText(el.innerText || el.textContent);
    alert('Copied to clipboard!');
  }
}

async function submitMessageFeedback(msgId, rating) {
  try {
    await fetch('/api/chat/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: currentSessionId,
        rating: rating
      })
    });
    alert('Thank you for your feedback!');
  } catch (e) {
    console.error(e);
  }
}

// Academic Hub Controller
async function filterAcademicSyllabus() {
  const course = document.getElementById('academic-course-filter').value;
  const sem = document.getElementById('academic-sem-filter').value;
  const query = document.getElementById('academic-keyword').value.trim();
  loadAcademicSyllabus(course, sem, query);
}

function syllabusResourcesHtml(data) {
  const items = (data.resources || []).map(r => `<a href="${r.url}" target="_blank" rel="noopener" class="block bg-white border border-slate-200 rounded-xl p-3 hover:border-blue-400"><span class="font-semibold text-slate-900 text-sm">${escapeHtml(r.title)}</span><span class="block text-xs text-slate-500">${escapeHtml(r.note || '')}</span></a>`).join('');
  return items ? `<div class="space-y-2"><p class="text-xs font-bold text-blue-600 uppercase tracking-wider">Official sources for your selection</p><div class="grid sm:grid-cols-2 gap-2">${items}</div></div>` : '';
}

async function loadAcademicSyllabus(course = 'BCA', sem = '5', query = '') {
  const container = document.getElementById('syllabus-results-container');
  if (!container) return;
  container.innerHTML = '<div class="p-6 text-center text-sm text-slate-400">Loading verified syllabus data...</div>';

  try {
    let url = `/api/academic/syllabus?`;
    if (course) url += `course=${encodeURIComponent(course)}&`;
    if (sem) url += `semester=${encodeURIComponent(sem)}&`;
    if (query) url += `query=${encodeURIComponent(query)}&`;

    const res = await fetch(url);
    const data = await res.json();

    if (!data.results || data.results.length === 0) {
      container.innerHTML = `<div class="bg-white p-6 rounded-2xl border border-slate-200 space-y-3"><p class="text-slate-600 font-medium">No stored syllabus document for this selection. Use the official sources below.</p>${syllabusResourcesHtml(data)}</div>`;
      return;
    }

    container.innerHTML = syllabusResourcesHtml(data) + data.results.map(r => `
      <div class="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-3">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <div>
            <span class="text-xs font-bold text-blue-600 uppercase tracking-wider">${r.department || 'Curriculum'} • Year ${r.academic_year || '2024-25'}</span>
            <h3 class="text-lg font-bold text-slate-900">${r.title}</h3>
          </div>
          <a href="${r.source_url}" target="_blank" class="badge-source">
            <i data-lucide="external-link" class="w-3.5 h-3.5"></i>
            <span>${r.source_title || 'PTU Portal'}</span>
          </a>
        </div>
        <p class="text-xs text-slate-600">${r.summary || ''}</p>
        <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs font-mono text-slate-800 whitespace-pre-line leading-relaxed max-h-64 overflow-y-auto">
          ${escapeHtml(r.content)}
        </div>
        <div class="flex items-center justify-between text-xs pt-1">
          <span class="text-slate-400">IKGPTU Board of Studies Approved</span>
          <button onclick="switchTab('chat'); preprompt('Explain topics from ${r.title}');" class="text-blue-700 font-semibold hover:underline flex items-center gap-1">
            <i data-lucide="sparkles" class="w-3.5 h-3.5"></i> Ask AI Tutor
          </button>
        </div>
      </div>
    `).join('');

    lucide.createIcons();
  } catch (err) {
    container.innerHTML = '<div class="text-rose-600 text-sm p-4">Error loading syllabus documents.</div>';
    console.error(err);
  }
}

// Generate Revision Notes
async function generateRevisionNotes() {
  const subject = document.getElementById('notes-subject').value.trim();
  const topic = document.getElementById('notes-topic').value.trim();
  const output = document.getElementById('revision-notes-output');
  output.classList.remove('hidden');
  output.innerHTML = '<div class="flex items-center gap-2 text-slate-500"><span class="ai-orb"></span> Generating structured revision notes...</div>';

  try {
    const res = await fetch('/api/academic/generate-notes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subject, topic, course: document.getElementById('academic-course-filter').value || null, semester: document.getElementById('academic-sem-filter').value || null })
    });
    const data = await res.json();
    output.innerHTML = `
      <div class="prose prose-sm max-w-none text-slate-800">
        ${marked.parse(data.notes)}
      </div>
    `;
  } catch (e) {
    output.innerHTML = '<div class="text-rose-600">Failed to generate notes.</div>';
  }
}

// Generate Practice Quiz
async function generatePracticeQuiz() {
  const subject = document.getElementById('quiz-subject').value;
  const output = document.getElementById('quiz-output');
  output.classList.remove('hidden');
  output.innerHTML = '<div class="text-sm text-slate-500">Loading quiz questions...</div>';

  try {
    const res = await fetch('/api/academic/quiz', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subject: subject, course: document.getElementById('academic-course-filter').value || null, semester: document.getElementById('academic-sem-filter').value || null, count: 5 })
    });
    const data = await res.json();
    
    if (!data.questions || !data.questions.length) { output.innerHTML = `<div class="text-sm text-slate-600 p-3">${escapeHtml(data.message || 'No questions available.')}</div>`; return; }
    output.innerHTML = data.questions.map((q, qIndex) => `
      <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2 text-sm">
        <div class="font-bold text-slate-900">Q${qIndex + 1}. ${escapeHtml(q.question)}</div>
        <div class="space-y-1.5 pt-1">
          ${q.options.map((opt, optIndex) => `
            <button onclick="checkQuizAnswer(this, ${optIndex}, ${q.correct_index}, '${escapeHtml(q.explanation)}')" class="w-full text-left px-3 py-2 rounded-lg bg-white border border-slate-200 hover:bg-blue-50 text-xs transition">
              ${escapeHtml(opt)}
            </button>
          `).join('')}
        </div>
        <div class="quiz-feedback hidden text-xs p-2.5 rounded-lg"></div>
      </div>
    `).join('');
  } catch (e) {
    output.innerHTML = '<div class="text-rose-600 text-sm">Failed to load quiz.</div>';
  }
}

function checkQuizAnswer(btn, selected, correct, explanation) {
  const parent = btn.closest('.space-y-2');
  const feedback = parent.querySelector('.quiz-feedback');
  feedback.classList.remove('hidden');

  if (selected === correct) {
    btn.classList.add('bg-emerald-100', 'border-emerald-400', 'text-emerald-900');
    feedback.className = 'quiz-feedback p-2.5 rounded-lg bg-emerald-50 text-emerald-800 text-xs';
    feedback.innerHTML = `<strong>Correct!</strong> ${explanation}`;
  } else {
    btn.classList.add('bg-rose-100', 'border-rose-400', 'text-rose-900');
    feedback.className = 'quiz-feedback p-2.5 rounded-lg bg-rose-50 text-rose-800 text-xs';
    feedback.innerHTML = `<strong>Incorrect.</strong> ${explanation}`;
  }
}

// Digital Library Controller
function filterLibrary(category) {
  document.querySelectorAll('.lib-filter-btn').forEach(btn => {
    btn.className = 'lib-filter-btn px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-slate-100 text-slate-700 hover:bg-slate-200 transition';
  });
  const activeBtn = document.getElementById(`lib-${category}`);
  if (activeBtn) {
    activeBtn.className = 'lib-filter-btn px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-blue-700 text-white transition';
  }
  loadLibraryResources(category);
}

async function loadLibraryResources(category = 'all') {
  const grid = document.getElementById('library-resources-grid');
  if (!grid) return;
  grid.innerHTML = '<div class="col-span-full p-8 text-center text-sm text-slate-400">Loading library resources...</div>';

  try {
    const res = await fetch(`/api/library/resources?category=${category}`);
    const data = await res.json();

    grid.innerHTML = data.resources.map(r => `
      <div class="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between feature-card">
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-[10px] uppercase font-bold text-cyan-600 bg-cyan-50 px-2 py-0.5 rounded-md border border-cyan-100">${r.type}</span>
            <i data-lucide="book-open" class="w-4 h-4 text-slate-400"></i>
          </div>
          <h3 class="font-bold text-slate-900 text-base">${r.title}</h3>
          <p class="text-slate-600 text-xs leading-relaxed">${r.description}</p>
        </div>
        <div class="mt-6 pt-4 border-t border-slate-100 space-y-2 text-xs">
          <div class="text-slate-500">Access Mode: <span class="font-semibold text-slate-700">${r.access}</span></div>
          <a href="${r.url}" target="_blank" class="w-full bg-slate-50 hover:bg-blue-50 text-blue-700 font-semibold py-2 px-3 rounded-lg border border-slate-200 flex items-center justify-center gap-1.5 transition">
            <span>Explore Repository</span>
            <i data-lucide="external-link" class="w-3.5 h-3.5"></i>
          </a>
        </div>
      </div>
    `).join('');

    lucide.createIcons();
  } catch (e) {
    grid.innerHTML = '<div class="text-rose-600 text-sm">Failed to load library data.</div>';
  }
}

// Course Explorer Controller
async function loadCourses() {
  const container = document.getElementById('courses-departments-container');
  if (!container) return;

  try {
    const res = await fetch('/api/courses');
    if (!res.ok) throw new Error('Server returned status ' + res.status);   // shows the message below + details in the console
    const data = await res.json();

    container.innerHTML = data.departments.map(dept => `
      <div class="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
        <div class="border-b border-slate-100 pb-3">
          <span class="text-xs font-bold text-indigo-600 uppercase tracking-wider">${dept.department_code}</span>
          <h3 class="text-xl font-bold text-slate-900">${dept.department}</h3>
          <p class="text-xs text-slate-500"><a href="${dept.category_url}" target="_blank" rel="noopener" class="text-blue-700 underline">Official category page</a></p>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          ${dept.programs.map(p => `
            <div class="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
              <div class="flex items-center justify-between">
                <span class="text-xs font-bold text-blue-700 bg-blue-100/60 px-2 py-0.5 rounded">${escapeHtml(p.level)}</span>
                <span class="text-xs text-slate-400 font-medium">${escapeHtml(p.duration)}</span>
              </div>
              <h4 class="font-bold text-slate-900 text-sm">${escapeHtml(p.name)}</h4>
              <p class="text-xs text-slate-600"><strong>Eligibility:</strong> ${escapeHtml(p.eligibility)}${p.approximate ? ' <em class="text-amber-700">(stored data, please confirm officially)</em>' : ''}</p>
              ${p.ptu_batches ? `<p class="text-xs text-slate-600"><strong>PTU syllabus batches:</strong> ${escapeHtml(p.ptu_batches)}</p>` : ''}
              ${p.features ? `<p class="text-[11px] text-slate-500">${escapeHtml(p.features)}</p>` : ''}
              <p class="text-xs">${p.cgc_url ? `<a href="${p.cgc_url}" target="_blank" rel="noopener" class="text-blue-700 underline">CGC programme page</a>` : '<span class="text-slate-400">No page link on the CGC site</span>'} · <a href="https://ptu.ac.in/syllabus" target="_blank" rel="noopener" class="text-blue-700 underline">PTU syllabus</a></p>
            </div>
          `).join('')}
        </div>
      </div>
    `).join('');
  } catch (e) {
    console.error('Courses error:', e);
    container.innerHTML = '<div class="text-rose-600 text-sm">Error loading course directory.</div>';
  }
}

// Escalation Form Submission
function openEscalationModal() {
  document.getElementById('modal-escalate').classList.remove('hidden');
  lucide.createIcons();
}
function closeEscalationModal() {
  document.getElementById('modal-escalate').classList.add('hidden');
}
async function handleEscalationSubmit(e) {
  e.preventDefault();
  const query = document.getElementById('escalate-query').value.trim();
  const email = document.getElementById('escalate-contact').value.trim();

  try {
    const res = await fetch('/api/chat/unresolved', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: currentSessionId,
        query: query,
        contact_email: email
      })
    });
    if (res.ok) {
      alert('Your inquiry has been registered with the Campus Help Desk.');
      closeEscalationModal();
      document.getElementById('escalate-query').value = '';
    }
  } catch (err) {
    alert('Failed to submit escalation.');
  }
}

// Admin Panel Controller
async function handleAdminLogin(e) {
  e.preventDefault();
  const username = document.getElementById('admin-username').value.trim();
  const password = document.getElementById('admin-password').value.trim();

  try {
    const res = await fetch('/api/admin/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    if (res.ok) {
      const data = await res.json();
      adminToken = data.access_token;
      localStorage.setItem('campusmind_admin_token', adminToken);
      showAdminPanel();
    } else {
      alert('Invalid username or password.');
    }
  } catch (err) {
    alert('Login error.');
  }
}

function handleAdminLogout() {
  adminToken = null;
  localStorage.removeItem('campusmind_admin_token');
  document.getElementById('admin-panel').classList.add('hidden');
  document.getElementById('admin-login-box').classList.remove('hidden');
}

function showAdminPanel() {
  document.getElementById('admin-login-box').classList.add('hidden');
  document.getElementById('admin-panel').classList.remove('hidden');
  loadAdminDocs();
  lucide.createIcons();
}

function switchAdminTab(subtab) {
  ['docs', 'feedback', 'unresolved', 'audit'].forEach(t => {
    document.getElementById(`adm-view-${t}`).classList.add('hidden');
    document.getElementById(`adm-tab-${t}`).className = 'px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-900';
  });
  document.getElementById(`adm-view-${subtab}`).classList.remove('hidden');
  document.getElementById(`adm-tab-${subtab}`).className = 'px-4 py-2 text-sm font-semibold border-b-2 border-blue-700 text-blue-700';

  if (subtab === 'docs') loadAdminDocs();
  if (subtab === 'feedback') loadAdminFeedback();
  if (subtab === 'unresolved') loadAdminUnresolved();
  if (subtab === 'audit') loadAdminAudit();
  lucide.createIcons();
}

async function loadAdminDocs() {
  const container = document.getElementById('admin-docs-table');
  try {
    const res = await fetch('/api/admin/documents', {
      headers: { 'Authorization': `Bearer ${adminToken}` }
    });
    if (res.ok) {
      const data = await res.json();
      document.getElementById('docs-count-badge').textContent = `${data.count} Documents`;
      container.innerHTML = `
        <table class="w-full text-left text-xs border-collapse">
          <thead>
            <tr class="bg-slate-50 border-b border-slate-200 text-slate-600">
              <th class="p-3">Title</th>
              <th class="p-3">Category</th>
              <th class="p-3">Department</th>
              <th class="p-3">Verified</th>
              <th class="p-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            ${data.documents.map(d => `
              <tr class="border-b border-slate-100 hover:bg-slate-50">
                <td class="p-3 font-semibold text-slate-900">${escapeHtml(d.title)}</td>
                <td class="p-3"><span class="bg-blue-50 text-blue-700 px-2 py-0.5 rounded font-mono">${d.category}</span></td>
                <td class="p-3 text-slate-600">${d.department || '-'}</td>
                <td class="p-3"><span class="text-emerald-700 font-bold">✓ Verified</span></td>
                <td class="p-3">
                  <button onclick="deleteAdminDoc('${d.id}')" class="text-rose-600 hover:underline">Delete</button>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `;
    }
  } catch (e) {
    container.innerHTML = '<div class="text-rose-600">Failed to load documents.</div>';
  }
}

async function deleteAdminDoc(id) {
  if (!confirm('Are you sure you want to remove this document from the knowledge base?')) return;
  try {
    await fetch(`/api/admin/documents/${id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${adminToken}` }
    });
    loadAdminDocs();
  } catch (e) {
    alert('Delete failed.');
  }
}

async function loadAdminFeedback() {
  const container = document.getElementById('admin-feedback-table');
  try {
    const res = await fetch('/api/admin/feedback', {
      headers: { 'Authorization': `Bearer ${adminToken}` }
    });
    const data = await res.json();
    container.innerHTML = `
      <table class="w-full text-left text-xs border-collapse">
        <thead>
          <tr class="bg-slate-50 border-b border-slate-200 text-slate-600">
            <th class="p-3">Session</th>
            <th class="p-3">Rating</th>
            <th class="p-3">Comment</th>
            <th class="p-3">Timestamp</th>
          </tr>
        </thead>
        <tbody>
          ${data.feedback.map(f => `
            <tr class="border-b border-slate-100">
              <td class="p-3 font-mono">${f.session_id || 'N/A'}</td>
              <td class="p-3 font-bold ${f.rating === 'helpful' ? 'text-emerald-600' : 'text-rose-600'}">${f.rating}</td>
              <td class="p-3 text-slate-600">${escapeHtml(f.comment || '-')}</td>
              <td class="p-3 text-slate-400">${f.created_at}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  } catch (e) {
    container.innerHTML = '<div class="text-rose-600">Failed to load feedback.</div>';
  }
}

async function loadAdminUnresolved() {
  const container = document.getElementById('admin-unresolved-table');
  try {
    const res = await fetch('/api/admin/unresolved', {
      headers: { 'Authorization': `Bearer ${adminToken}` }
    });
    const data = await res.json();
    container.innerHTML = `
      <table class="w-full text-left text-xs border-collapse">
        <thead>
          <tr class="bg-slate-50 border-b border-slate-200 text-slate-600">
            <th class="p-3">Query</th>
            <th class="p-3">Contact</th>
            <th class="p-3">Status</th>
            <th class="p-3">Action</th>
          </tr>
        </thead>
        <tbody>
          ${data.unresolved_queries.map(u => `
            <tr class="border-b border-slate-100">
              <td class="p-3 font-medium text-slate-900">${escapeHtml(u.query)}</td>
              <td class="p-3 font-mono text-slate-600">${escapeHtml(u.contact_email || '-')}</td>
              <td class="p-3"><span class="px-2 py-0.5 rounded text-[11px] font-bold ${u.status === 'resolved' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">${u.status}</span></td>
              <td class="p-3">
                ${u.status !== 'resolved' ? `<button onclick="resolveQuery(${u.id})" class="text-blue-600 hover:underline">Mark Resolved</button>` : '-'}
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  } catch (e) {
    container.innerHTML = '<div class="text-rose-600">Failed to load inquiries.</div>';
  }
}

async function resolveQuery(id) {
  try {
    await fetch(`/api/admin/unresolved/${id}/resolve`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${adminToken}` }
    });
    loadAdminUnresolved();
  } catch (e) {
    alert('Failed to resolve query.');
  }
}

async function loadAdminAudit() {
  const container = document.getElementById('admin-audit-table');
  try {
    const res = await fetch('/api/admin/audit-logs', {
      headers: { 'Authorization': `Bearer ${adminToken}` }
    });
    const data = await res.json();
    container.innerHTML = `
      <table class="w-full text-left text-xs border-collapse">
        <thead>
          <tr class="bg-slate-50 border-b border-slate-200 text-slate-600">
            <th class="p-3">User</th>
            <th class="p-3">Action</th>
            <th class="p-3">Target</th>
            <th class="p-3">Details</th>
            <th class="p-3">Time</th>
          </tr>
        </thead>
        <tbody>
          ${data.audit_logs.map(a => `
            <tr class="border-b border-slate-100">
              <td class="p-3 font-bold text-slate-900">${a.admin_user}</td>
              <td class="p-3 font-mono text-blue-700">${a.action}</td>
              <td class="p-3 text-slate-700">${escapeHtml(a.target || '-')}</td>
              <td class="p-3 text-slate-500">${escapeHtml(a.details || '-')}</td>
              <td class="p-3 text-slate-400">${a.timestamp}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  } catch (e) {
    container.innerHTML = '<div class="text-rose-600">Failed to load audit logs.</div>';
  }
}

// Upload Modal Controller
function openUploadModal() {
  document.getElementById('modal-upload').classList.remove('hidden');
  lucide.createIcons();
}
function closeUploadModal() {
  document.getElementById('modal-upload').classList.add('hidden');
}
async function handleDocumentUpload(e) {
  e.preventDefault();
  const fileInput = document.getElementById('upload-file');
  const category = document.getElementById('upload-category').value;
  const dept = document.getElementById('upload-department').value;

  if (!fileInput.files || fileInput.files.length === 0) return;

  const formData = new FormData();
  formData.append('file', fileInput.files[0]);
  formData.append('category', category);
  formData.append('department', dept);

  try {
    const res = await fetch('/api/admin/upload', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${adminToken}` },
      body: formData
    });
    if (res.ok) {
      alert('Document successfully uploaded and indexed into Knowledge Base!');
      closeUploadModal();
      loadAdminDocs();
    } else {
      alert('Upload failed.');
    }
  } catch (err) {
    alert('Upload error.');
  }
}

// Utility: HTML Escape
function escapeHtml(text) {
  if (!text) return '';
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
