// Client-side Logic for the comprehensive student portal

document.addEventListener('DOMContentLoaded', () => {
    // Load user profile for the header
    loadProfile();
    // Load notifications count
    loadNotifications();
    // Initial fetch for active tab (Classes)
    loadClasses();
});

const titles = {
    'classes': 'My Classes & Materials',
    'students': 'Classmates & Leaderboard',
    'attendance': 'Attendance Overview',
    'reports': 'Performance Reports & AI Insights',
    'assignments': 'Assignments & Tasks',
    'exams': 'Exams & Quizzes',
    'achievements': 'My Achievements',
    'analytics': 'Learning Analytics'
};

function switchTab(tabId) {
    // UI states
    document.querySelectorAll('.nav-btn').forEach(b => {
        b.classList.remove('nav-active');
        b.style.borderRight = 'none';
    });
    
    const activeBtn = document.getElementById('tab-' + tabId);
    activeBtn.classList.add('nav-active');
    activeBtn.style.borderRight = '3px solid #4f46e5';
    
    document.getElementById('page-title').innerText = titles[tabId];
    
    document.querySelectorAll('.section-content').forEach(s => s.classList.remove('active-section'));
    document.getElementById('sec-' + tabId).classList.add('active-section');
    
    // Load Data dynamically
    if(tabId === 'classes') loadClasses();
    if(tabId === 'students') loadClassmates();
    if(tabId === 'attendance') loadAttendance();
    if(tabId === 'reports') loadReports();
    if(tabId === 'assignments') loadAssignments();
    if(tabId === 'exams') loadExams();
    if(tabId === 'achievements') loadAchievements();
    if(tabId === 'analytics') loadAnalytics();
}

// ─── USER PROFILE ────────────────────────────────────────────
function loadProfile() {
    fetch('/api/portal/profile').then(r => r.json()).then(data => {
        if (!data.success) return;
        const p = data.data;
        const nameEl = document.getElementById('header-username');
        const avatarEl = document.getElementById('header-avatar');
        if (nameEl) nameEl.textContent = p.full_name || 'Student';
        if (avatarEl) avatarEl.src = `https://ui-avatars.com/api/?name=${(p.full_name || 'Student').replace(' ', '+')}&background=4f46e5&color=fff`;
    }).catch(() => {});
}

// ─── NOTIFICATIONS ───────────────────────────────────────────
let notificationsData = [];

function loadNotifications() {
    fetch('/api/portal/notifications').then(r => r.json()).then(data => {
        if (!data.success) return;
        notificationsData = data.data.notifications;
        const badge = document.getElementById('notif-badge');
        const count = data.data.unread_count;
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'flex' : 'none';
        }
    }).catch(() => {});
}

function toggleNotifications() {
    const panel = document.getElementById('notif-panel');
    if (!panel) return;
    
    if (panel.classList.contains('hidden')) {
        // Populate notifications
        let html = notificationsData.length === 0 
            ? '<p class="text-center text-gray-400 py-6">No notifications</p>'
            : notificationsData.map(n => `
                <div class="flex gap-3 p-3 rounded-lg ${n.read ? 'bg-white' : 'bg-blue-50'} hover:bg-gray-50 transition-colors cursor-pointer" onclick="markNotifRead(${n.id})">
                    <div class="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 ${n.read ? 'bg-gray-100 text-gray-500' : 'bg-blue-100 text-blue-600'}">
                        <span class="material-icons-outlined text-[18px]">${n.icon}</span>
                    </div>
                    <div class="flex-1 min-w-0">
                        <p class="text-sm font-semibold text-gray-800 ${n.read ? '' : 'text-blue-900'}">${n.title}</p>
                        <p class="text-xs text-gray-500 truncate">${n.message}</p>
                        <p class="text-[10px] text-gray-400 mt-1">${n.time}</p>
                    </div>
                    ${!n.read ? '<div class="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>' : ''}
                </div>
            `).join('');
        
        document.getElementById('notif-list').innerHTML = html;
        panel.classList.remove('hidden');
    } else {
        panel.classList.add('hidden');
    }
}

function markNotifRead(id) {
    fetch(`/api/portal/notifications/${id}/read`, { method: 'POST' }).then(() => {
        const notif = notificationsData.find(n => n.id === id);
        if (notif) notif.read = true;
        const unread = notificationsData.filter(n => !n.read).length;
        const badge = document.getElementById('notif-badge');
        if (badge) {
            badge.textContent = unread;
            badge.style.display = unread > 0 ? 'flex' : 'none';
        }
        toggleNotifications();
        toggleNotifications();
    });
}

// Close notifications when clicking outside
document.addEventListener('click', (e) => {
    const panel = document.getElementById('notif-panel');
    const btn = document.getElementById('notif-btn');
    if (panel && !panel.classList.contains('hidden') && !panel.contains(e.target) && !btn.contains(e.target)) {
        panel.classList.add('hidden');
    }
});

// ─── CLASSES ─────────────────────────────────────────────────
function loadClasses() {
    fetch('/api/portal/classes').then(r=>r.json()).then(data => {
        if(!data.success) return;
        let html = '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">';
        data.data.forEach(cls => {
            html += `
                <div class="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow group">
                    <div class="flex justify-between items-start mb-4">
                        <div>
                            <h3 class="text-xl font-bold text-gray-800 group-hover:text-primary transition-colors">${cls.name}</h3>
                            <p class="text-sm text-gray-500">${cls.teacher}</p>
                        </div>
                        <span class="bg-blue-50 text-blue-600 px-3 py-1 rounded-full text-xs font-bold">${cls.progress}% Progress</span>
                    </div>
                    
                    <div class="mb-4">
                        <div class="w-full bg-gray-100 rounded-full h-1.5">
                            <div class="bg-gradient-to-r from-blue-500 to-indigo-500 h-1.5 rounded-full" style="width: ${cls.progress}%"></div>
                        </div>
                    </div>
                    
                    <div class="bg-orange-50 border border-orange-100 rounded-lg p-3 mb-4">
                        <p class="text-xs text-orange-800 font-medium">⚠️ Upcoming: ${cls.upcoming}</p>
                    </div>
                    
                    <div class="space-y-2 mb-5">
                        <p class="text-xs font-bold text-gray-400 uppercase tracking-wider">Materials</p>
                        ${cls.materials.map(m => `
                            <a href="#" onclick="showToast('📄 Downloading ${m}...', 'info'); return false;" class="flex items-center gap-2 text-sm text-gray-600 hover:text-primary transition-colors">
                                <span class="material-icons-outlined text-[16px]">picture_as_pdf</span> ${m}
                            </a>
                        `).join('')}
                    </div>
                    <div class="pt-4 border-t border-gray-100 flex gap-2">
                        <button onclick="openAITutor('${cls.name}')" class="flex-1 flex justify-center items-center gap-2 bg-green-50 hover:bg-green-100 text-green-700 py-2 rounded-lg text-sm font-semibold transition-colors">
                            <span class="material-icons-outlined text-[16px]">smart_toy</span> AI Tutor
                        </button>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        document.getElementById('sec-classes').innerHTML = html;
    });
}



function openAITutor(className) {
    // Open the chatbot with subject context
    const cb = document.getElementById('chatbot');
    if (!cb.classList.contains('open')) cb.classList.add('open');
    const input = document.getElementById('chat-input');
    input.value = `Help me study ${className}`;
    sendMsg();
}

// ─── CLASSMATES ──────────────────────────────────────────────
let classmatesData = [];
let activeClassmateView = 'directory';

function loadClassmates() {
    fetch('/api/portal/classmates').then(r=>r.json()).then(data => {
        if(!data.success) return;
        classmatesData = data.data;
        renderClassmatesView();
    });
}

function switchClassmateView(view) {
    activeClassmateView = view;
    renderClassmatesView();
}

function renderClassmatesView() {
    const data = classmatesData;
    if (!data || data.length === 0) return;

    const dirActive = activeClassmateView === 'directory';
    const lbActive = activeClassmateView === 'leaderboard';

    let tabsHtml = `
        <div class="mb-6 flex gap-4">
            <button onclick="switchClassmateView('directory')" class="${dirActive ? 'bg-primary text-white shadow' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'} px-4 py-2 rounded-lg font-medium transition-colors">Class Directory</button>
            <button onclick="switchClassmateView('leaderboard')" class="${lbActive ? 'bg-primary text-white shadow' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'} px-4 py-2 rounded-lg font-medium transition-colors">Leaderboard Rankings</button>
            <button onclick="createStudyRoom()" class="bg-white text-gray-600 border border-gray-200 px-4 py-2 rounded-lg font-medium shadow-sm ml-auto flex items-center gap-2 hover:bg-gray-50">
                <span class="material-icons-outlined text-[18px]">add</span> Create Study Room
            </button>
        </div>
    `;

    let contentHtml = '';

    if (dirActive) {
        contentHtml = `
            <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="bg-gray-50 text-gray-500 text-sm uppercase">
                            <th class="p-4 font-semibold">#</th>
                            <th class="p-4 font-semibold">Student</th>
                            <th class="p-4 font-semibold">Section</th>
                            <th class="p-4 font-semibold text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100">
                        ${data.map((c, i) => `
                            <tr class="hover:bg-gray-50 transition-colors">
                                <td class="p-4 text-center w-16">
                                    <span class="font-bold text-gray-400">${i + 1}</span>
                                </td>
                                <td class="p-4 flex items-center gap-3">
                                    <img src="https://ui-avatars.com/api/?name=${c.full_name.replace(' ', '+')}&background=random" class="w-10 h-10 rounded-full">
                                    <div>
                                        <p class="font-bold text-gray-800">${c.full_name}</p>
                                        <p class="text-xs text-gray-500">${c.student_id}</p>
                                    </div>
                                </td>
                                <td class="p-4 text-gray-600">${c.section}</td>
                                <td class="p-4 text-right">
                                    <button onclick="messageStudent('${c.full_name}')" class="text-blue-600 hover:bg-blue-50 p-2 rounded-full transition-colors" title="Message">
                                        <span class="material-icons-outlined text-[20px]">chat</span>
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    } else {
        const topThree = data.slice(0, 3);
        const rest = data.slice(3);

        contentHtml = `
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                ${topThree.map((s, i) => {
                    const colors = [
                        {bg: 'from-yellow-400 to-amber-500', ring: 'ring-yellow-300', icon: '🥇'},
                        {bg: 'from-gray-300 to-slate-400', ring: 'ring-gray-300', icon: '🥈'},
                        {bg: 'from-orange-400 to-amber-600', ring: 'ring-orange-300', icon: '🥉'}
                    ];
                    const c = colors[i];
                    return `
                    <div class="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm text-center hover:shadow-md transition-shadow relative overflow-hidden ${i === 0 ? 'md:order-2 md:scale-105 md:shadow-lg' : i === 1 ? 'md:order-1' : 'md:order-3'}">
                        <div class="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r ${c.bg}"></div>
                        <div class="text-4xl mb-2">${c.icon}</div>
                        <div class="relative inline-block mb-3">
                            <img src="https://ui-avatars.com/api/?name=${s.full_name.replace(' ', '+')}&background=4f46e5&color=fff&size=80" class="w-16 h-16 rounded-full ring-4 ${c.ring} shadow-md">
                        </div>
                        <h4 class="font-bold text-gray-800 text-lg">${s.full_name}</h4>
                        <p class="text-xs text-gray-500 mb-3">${s.student_id}</p>
                        <div class="flex justify-center gap-4 text-sm mb-3">
                            <div>
                                <p class="text-xs text-gray-400 uppercase font-semibold">GPA</p>
                                <p class="font-extrabold text-indigo-600 text-lg">${(s.gpa || 0).toFixed(1)}</p>
                            </div>
                            <div class="border-l border-gray-200 pl-4">
                                <p class="text-xs text-gray-400 uppercase font-semibold">Attend.</p>
                                <p class="font-extrabold ${(s.attendance_pct || 0) >= 90 ? 'text-green-600' : (s.attendance_pct || 0) >= 75 ? 'text-yellow-600' : 'text-red-600'} text-lg">${(s.attendance_pct || 0).toFixed(0)}%</p>
                            </div>
                        </div>
                        <div class="flex flex-wrap justify-center gap-1">
                            ${(s.badges || []).map(b => `<span class="bg-yellow-50 border border-yellow-200 text-yellow-700 text-[10px] px-2 py-0.5 rounded-full font-semibold">${b}</span>`).join('')}
                        </div>
                    </div>`;
                }).join('')}
            </div>
            <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="bg-gray-50 text-gray-500 text-sm uppercase">
                            <th class="p-4 font-semibold text-center w-16">Rank</th>
                            <th class="p-4 font-semibold">Student</th>
                            <th class="p-4 font-semibold">Section</th>
                            <th class="p-4 font-semibold text-center">GPA</th>
                            <th class="p-4 font-semibold text-center">Attendance</th>
                            <th class="p-4 font-semibold text-center">Score</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100">
                        ${rest.map(c => {
                            const score = Math.round(((c.gpa || 0) / 4.0 * 60) + ((c.attendance_pct || 0) / 100 * 40));
                            const attColor = (c.attendance_pct || 0) >= 90 ? 'text-green-600' : (c.attendance_pct || 0) >= 75 ? 'text-yellow-600' : 'text-red-600';
                            return `
                            <tr class="hover:bg-gray-50 transition-colors">
                                <td class="p-4 text-center"><span class="font-bold text-gray-400">#${c.rank}</span></td>
                                <td class="p-4 flex items-center gap-3">
                                    <img src="https://ui-avatars.com/api/?name=${c.full_name.replace(' ', '+')}&background=random" class="w-10 h-10 rounded-full">
                                    <div>
                                        <p class="font-bold text-gray-800">${c.full_name}</p>
                                        <p class="text-xs text-gray-500">${c.student_id}</p>
                                    </div>
                                    <div class="ml-2 flex gap-1 hidden sm:flex">
                                        ${(c.badges || []).map(b => `<span class="bg-yellow-50 border border-yellow-200 text-yellow-700 text-[10px] px-2 py-0.5 rounded-full font-semibold">${b}</span>`).join('')}
                                    </div>
                                </td>
                                <td class="p-4 text-gray-600">${c.section}</td>
                                <td class="p-4 text-center font-bold text-indigo-600">${(c.gpa || 0).toFixed(1)}</td>
                                <td class="p-4 text-center font-bold ${attColor}">${(c.attendance_pct || 0).toFixed(0)}%</td>
                                <td class="p-4 text-center">
                                    <div class="flex items-center gap-2 justify-center">
                                        <div class="w-20 bg-gray-100 rounded-full h-2">
                                            <div class="bg-gradient-to-r from-blue-500 to-indigo-500 h-2 rounded-full" style="width: ${score}%"></div>
                                        </div>
                                        <span class="text-sm font-bold text-gray-600">${score}</span>
                                    </div>
                                </td>
                            </tr>`;
                        }).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    document.getElementById('sec-students').innerHTML = tabsHtml + contentHtml;
}

function messageStudent(name) {
    showToast(`💬 Opening chat with ${name}...`, 'info');
    const cb = document.getElementById('chatbot');
    if (!cb.classList.contains('open')) cb.classList.add('open');
}

function createStudyRoom() {
    showToast('🎓 Study Room created! Share the link with classmates.', 'success');
}

// ─── ATTENDANCE ──────────────────────────────────────────────
function loadAttendance() {
    fetch('/api/portal/attendance_dashboard').then(r=>r.json()).then(data => {
        if(!data.success) return;
        const d = data.data;
        
        let subHtml = Object.keys(d.subjects).map(s => `
            <div class="flex items-center justify-between p-3 border border-gray-100 rounded-xl mb-2">
                <span class="font-semibold text-gray-700">${s}</span>
                <span class="font-bold ${d.subjects[s] < 75 ? 'text-red-500' : 'text-green-500'}">${d.subjects[s]}%</span>
            </div>
        `).join('');
        
        let histHtml = d.history.map(h => `
             <tr class="border-b border-gray-50">
                 <td class="py-3 text-gray-500 text-sm font-medium">${h.date}</td>
                 <td class="py-3 font-semibold text-gray-800">${h.subject}</td>
                 <td class="py-3 text-right">
                     <span class="${h.status==='Present' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'} px-2 py-1 rounded text-xs font-bold uppercase tracking-wider">${h.status}</span>
                 </td>
             </tr>
        `).join('');

        let html = `
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm col-span-1 md:col-span-2 flex flex-col justify-center items-center text-center">
                    <h3 class="text-gray-500 font-semibold mb-2 uppercase tracking-wide">Overall Attendance</h3>
                    <div class="relative w-40 h-40 flex items-center justify-center">
                        <svg class="w-full h-full transform -rotate-90">
                            <circle cx="80" cy="80" r="70" class="stroke-gray-100" stroke-width="12" fill="none"></circle>
                            <circle cx="80" cy="80" r="70" class="stroke-blue-500" stroke-width="12" fill="none" stroke-dasharray="439.8" stroke-dashoffset="${439.8 - (439.8 * d.overall / 100)}" stroke-linecap="round"></circle>
                        </svg>
                        <div class="absolute text-3xl font-extrabold text-gray-800">${d.overall}%</div>
                    </div>
                    
                    <div class="mt-6 w-full max-w-md bg-blue-50 border border-blue-100 rounded-xl p-4 flex gap-3 text-left">
                        <span class="material-icons-outlined text-blue-600 mt-0.5">auto_awesome</span>
                        <p class="text-sm font-medium text-blue-900">${d.prediction}</p>
                    </div>
                </div>
                
                <div class="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                    <h3 class="font-bold text-gray-800 mb-4">Subject-wise</h3>
                    ${subHtml}
                </div>
            </div>
            
            <div class="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm mt-6">
                <h3 class="font-bold text-gray-800 mb-4 text-lg">Detailed History</h3>
                <table class="w-full text-left">
                    ${histHtml}
                </table>
            </div>
        `;
        document.getElementById('sec-attendance').innerHTML = html;
    });
}

// ─── REPORTS ─────────────────────────────────────────────────
function loadReports() {
    document.getElementById('sec-reports').innerHTML = `<div class="flex flex-col items-center justify-center py-12 text-gray-500"><span class="material-icons-outlined text-4xl animate-pulse text-indigo-400 mb-2">psychology</span><p>AI is analyzing your performance...</p></div>`;
    fetch('/api/portal/reports').then(r=>r.json()).then(data => {
        if(!data.success) return;
        const d = data.data;
        
        let recs = d.recommendations.map(r => `
            <li class="flex items-start gap-3 bg-indigo-50 p-3 rounded-lg border border-indigo-100">
                <span class="material-icons-outlined text-indigo-500">play_circle</span>
                <span class="text-sm font-medium text-indigo-900">${r}</span>
            </li>
        `).join('');

        let html = `
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                 <div class="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-gray-100 p-8 relative overflow-hidden">
                    <div class="absolute -right-10 -top-10 text-gray-50 opacity-20">
                        <span class="material-icons-outlined text-[200px]">military_tech</span>
                    </div>
                    <div class="flex gap-3 items-center mb-6">
                        <div class="bg-gradient-to-r from-purple-500 to-indigo-500 text-white p-2 rounded-lg shadow-inner">
                            <span class="material-icons-outlined">psychology</span>
                        </div>
                        <h3 class="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-gray-800 to-gray-600">AI Deep Dive</h3>
                    </div>
                    
                    <div class="grid grid-cols-2 gap-6 relative z-10">
                        <div class="bg-green-50/50 p-5 rounded-xl border border-green-100">
                            <h4 class="text-xs font-bold uppercase tracking-wider text-green-600 mb-2">Greatest Strength</h4>
                            <p class="text-lg font-bold text-gray-800">${d.ai_insights.strength}</p>
                        </div>
                        <div class="bg-orange-50/50 p-5 rounded-xl border border-orange-100">
                            <h4 class="text-xs font-bold uppercase tracking-wider text-orange-600 mb-2">Needs Improvement</h4>
                            <p class="text-lg font-bold text-gray-800">${d.ai_insights.needs_improvement}</p>
                            <p class="text-sm text-gray-500 mt-2">Gap: ${d.ai_insights.gap}</p>
                        </div>
                    </div>
                </div>
                
                <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 flex flex-col">
                    <h3 class="font-bold text-gray-800 mb-4 flex items-center gap-2">
                        <span class="material-icons-outlined text-indigo-500">route</span> AI Study Plan
                    </h3>
                    <ul class="space-y-3 flex-1">
                        ${recs}
                    </ul>
                    <button onclick="downloadReport()" class="w-full mt-4 bg-gray-900 text-white py-3 rounded-xl font-bold hover:bg-gray-800 transition-colors shadow-lg flex justify-center items-center gap-2">
                        <span class="material-icons-outlined text-[18px]">file_download</span> Download PDF Report
                    </button>
                </div>
            </div>
        `;
        document.getElementById('sec-reports').innerHTML = html;
    });
}

function downloadReport() {
    showToast('📄 Generating your PDF report...', 'info');
    
    // Fetch all needed data
    Promise.all([
        fetch('/api/portal/profile').then(r => r.json()),
        fetch('/api/portal/reports').then(r => r.json()),
        fetch('/api/portal/attendance_dashboard').then(r => r.json()),
        fetch('/api/portal/achievements').then(r => r.json())
    ]).then(([profileRes, reportRes, attendRes, achieveRes]) => {
        const p = profileRes.success ? profileRes.data : {};
        const r = reportRes.success ? reportRes.data : {};
        const a = attendRes.success ? attendRes.data : {};
        const ach = achieveRes.success ? achieveRes.data : {};
        const stats = ach.stats || {};
        const earnedBadges = (ach.achievements || []).filter(x => x.earned);
        
        const now = new Date();
        const dateStr = now.toLocaleDateString('en-IN', { day:'2-digit', month:'long', year:'numeric' });
        const timeStr = now.toLocaleTimeString('en-IN', { hour:'2-digit', minute:'2-digit' });
        
        const gpaColor = (r.gpa || 0) >= 3.5 ? '#16a34a' : (r.gpa || 0) >= 2.5 ? '#d97706' : '#dc2626';
        const attColor = (a.overall || 0) >= 90 ? '#16a34a' : (a.overall || 0) >= 75 ? '#d97706' : '#dc2626';
        
        const recHtml = (r.recommendations || []).map((rec, i) =>
            `<div style="display:flex;align-items:flex-start;gap:10px;padding:8px 12px;background:#eef2ff;border-left:3px solid #4f46e5;border-radius:6px;margin-bottom:8px;">
                <span style="font-weight:bold;color:#4f46e5;min-width:20px;">${i+1}.</span>
                <span style="color:#1e1b4b;font-size:13px;">${rec}</span>
             </div>`).join('');
        
        const subjectRows = Object.entries(a.subjects || {}).map(([sub, pct]) =>
            `<tr>
                <td style="padding:8px 12px;font-weight:600;color:#374151;">${sub}</td>
                <td style="padding:8px 12px;text-align:center;">
                    <div style="background:#f3f4f6;border-radius:20px;height:8px;width:100%;overflow:hidden;">
                        <div style="background:${pct >= 75 ? '#16a34a' : '#dc2626'};height:100%;width:${pct}%;border-radius:20px;"></div>
                    </div>
                </td>
                <td style="padding:8px 12px;text-align:right;font-weight:bold;color:${pct >= 75 ? '#16a34a' : '#dc2626'};">${pct}%</td>
             </tr>`).join('');
        
        const badgeHtml = earnedBadges.slice(0, 6).map(b =>
            `<span style="background:#f0f9ff;border:1px solid #bae6fd;color:#0369a1;padding:4px 10px;border-radius:20px;font-size:11px;font-weight:600;">✓ ${b.title}</span>`
        ).join('');
        
        const htmlContent = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Student Performance Report - ${p.full_name || 'Student'}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Arial, sans-serif; background: white; color: #111827; }
        .page { max-width: 800px; margin: 0 auto; padding: 40px; }
        
        /* Header */
        .header { background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); color: white; padding: 32px 40px; border-radius: 16px; margin-bottom: 28px; display: flex; justify-content: space-between; align-items: flex-start; }
        .header-left h1 { font-size: 26px; font-weight: 800; letter-spacing: -0.5px; }
        .header-left p { opacity: 0.85; font-size: 13px; margin-top: 4px; }
        .header-right { text-align: right; }
        .header-right .school-name { font-size: 18px; font-weight: 700; }
        .header-right .report-date { font-size: 11px; opacity: 0.8; margin-top: 4px; }
        .student-id-badge { display: inline-block; background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; margin-top: 8px; }
        
        /* Section */
        .section { background: white; border: 1px solid #e5e7eb; border-radius: 12px; padding: 24px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
        .section-title { font-size: 14px; font-weight: 700; color: #6b7280; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 16px; padding-bottom: 10px; border-bottom: 2px solid #f3f4f6; display: flex; align-items: center; gap: 8px; }
        
        /* KPI Grid */
        .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
        .kpi-card { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 10px; padding: 16px; text-align: center; }
        .kpi-label { font-size: 10px; font-weight: 700; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
        .kpi-value { font-size: 24px; font-weight: 800; }
        
        /* AI Insights */
        .insights-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
        .insight-card { padding: 16px; border-radius: 10px; }
        .insight-card.strength { background: #f0fdf4; border: 1px solid #bbf7d0; }
        .insight-card.improve { background: #fff7ed; border: 1px solid #fed7aa; }
        .insight-label { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
        .insight-card.strength .insight-label { color: #16a34a; }
        .insight-card.improve .insight-label { color: #d97706; }
        .insight-value { font-size: 16px; font-weight: 700; color: #111827; }
        .insight-gap { font-size: 12px; color: #6b7280; margin-top: 6px; }
        
        /* Table */
        table { width: 100%; border-collapse: collapse; }
        th { padding: 10px 12px; background: #f9fafb; font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; text-align: left; border-bottom: 2px solid #e5e7eb; }
        
        /* Attendance circle */
        .att-circle-wrap { display: flex; align-items: center; gap: 24px; }
        .att-circle { width: 100px; height: 100px; border-radius: 50%; background: conic-gradient(${attColor} ${(a.overall||0)}%, #e5e7eb 0%); display: flex; align-items: center; justify-content: center; font-size: 20px; font-weight: 800; color: ${attColor}; position: relative; }
        .att-circle::before { content: ''; position: absolute; width: 80px; height: 80px; background: white; border-radius: 50%; }
        .att-circle span { position: relative; z-index: 1; }
        
        /* Badges */
        .badges-wrap { display: flex; flex-wrap: wrap; gap: 8px; }
        
        /* Footer */
        .footer { text-align: center; color: #9ca3af; font-size: 11px; margin-top: 32px; padding-top: 16px; border-top: 1px solid #e5e7eb; }
        
        @media print {
            body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
            .page { padding: 20px; }
        }
    </style>
</head>
<body>
<div class="page">
    <!-- Header -->
    <div class="header">
        <div class="header-left">
            <h1>${p.full_name || 'Student'}</h1>
            <p>Grade ${p.grade || 'N/A'} &bull; Section ${p.section || 'N/A'}</p>
            <span class="student-id-badge">ID: ${p.student_id || 'N/A'}</span>
        </div>
        <div class="header-right">
            <div class="school-name">📚 EduSync</div>
            <div class="report-date">Performance Report</div>
            <div class="report-date">${dateStr} at ${timeStr}</div>
        </div>
    </div>

    <!-- Key Metrics -->
    <div class="section">
        <div class="section-title">📊 Key Performance Indicators</div>
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label">GPA</div>
                <div class="kpi-value" style="color:${gpaColor};">${(r.gpa || 0).toFixed(2)}</div>
                <div style="font-size:11px;color:#9ca3af;margin-top:4px;">out of 4.0</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Attendance</div>
                <div class="kpi-value" style="color:${attColor};">${(a.overall || 0).toFixed(1)}%</div>
                <div style="font-size:11px;color:#9ca3af;margin-top:4px;">Overall rate</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Class Rank</div>
                <div class="kpi-value" style="color:#4f46e5;">#${r.rank || 'N/A'}</div>
                <div style="font-size:11px;color:#9ca3af;margin-top:4px;">in class</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Badges</div>
                <div class="kpi-value" style="color:#d97706;">${stats.total_earned || 0}/${stats.total_available || 0}</div>
                <div style="font-size:11px;color:#9ca3af;margin-top:4px;">earned</div>
            </div>
        </div>
    </div>

    <!-- AI Insights -->
    <div class="section">
        <div class="section-title">🤖 AI Performance Analysis</div>
        <div class="insights-grid">
            <div class="insight-card strength">
                <div class="insight-label">Greatest Strength</div>
                <div class="insight-value">${(r.ai_insights || {}).strength || 'N/A'}</div>
            </div>
            <div class="insight-card improve">
                <div class="insight-label">Needs Improvement</div>
                <div class="insight-value">${(r.ai_insights || {}).needs_improvement || 'N/A'}</div>
                <div class="insight-gap">${(r.ai_insights || {}).gap || ''}</div>
            </div>
        </div>
    </div>

    <!-- Subject Attendance -->
    <div class="section">
        <div class="section-title">📅 Subject-wise Attendance</div>
        <table>
            <thead><tr><th>Subject</th><th>Progress Bar</th><th style="text-align:right;">Rate</th></tr></thead>
            <tbody>${subjectRows}</tbody>
        </table>
        <div style="margin-top:14px;padding:12px 16px;background:#eff6ff;border-radius:8px;font-size:12px;color:#1e40af;border-left:3px solid #3b82f6;">
            <strong>AI Prediction:</strong> ${a.prediction || 'N/A'}
        </div>
    </div>

    <!-- AI Study Recommendations -->
    <div class="section">
        <div class="section-title">📚 AI Study Plan & Recommendations</div>
        ${recHtml || '<p style="color:#9ca3af;font-size:13px;">No recommendations available.</p>'}
    </div>

    <!-- Achievements -->
    ${earnedBadges.length > 0 ? `
    <div class="section">
        <div class="section-title">🏆 Earned Achievements</div>
        <div class="badges-wrap">${badgeHtml}</div>
        <div style="margin-top:12px;font-size:12px;color:#6b7280;">XP Points: <strong style="color:#4f46e5;">${stats.xp_points || 0}</strong> &bull; Level: <strong style="color:#4f46e5;">${stats.level || 1}</strong></div>
    </div>` : ''}

    <!-- Footer -->
    <div class="footer">
        <p>This report was automatically generated by <strong>EduSync Smart Classroom Platform</strong></p>
        <p style="margin-top:4px;">Generated on ${dateStr} at ${timeStr} &bull; Confidential Academic Record</p>
    </div>
</div>
<script>window.onload = function() { window.print(); };</script>
</body>
</html>`;
        
        const printWindow = window.open('', '_blank', 'width=900,height=700');
        if (!printWindow) {
            showToast('❌ Pop-up blocked. Please allow pop-ups to download the report.', 'error');
            return;
        }
        printWindow.document.write(htmlContent);
        printWindow.document.close();
        showToast('✅ PDF Report opened! Use "Save as PDF" in the print dialog.', 'success');
        
    }).catch(err => {
        console.error('Report generation error:', err);
        showToast('❌ Failed to generate report. Please try again.', 'error');
    });
}

// ─── ASSIGNMENTS ─────────────────────────────────────────────
function loadAssignments() {
     fetch('/api/portal/assignments').then(r=>r.json()).then(data => {
         if(!data.success) return;
         let html = data.data.map(a => `
             <div class="flex items-center justify-between p-4 border border-gray-100 rounded-xl hover:bg-slate-50 transition-colors" id="assignment-${a.id}">
                 <div>
                     <h4 class="font-bold text-gray-800 text-lg">${a.title}</h4>
                     <p class="text-sm text-gray-500 font-medium">${a.subject} • Due: ${a.due_date}</p>
                 </div>
                 ${a.status === 'pending' 
                   ? `<button onclick="submitAssignment(${a.id}, '${a.title}')" class="bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold text-sm shadow hover:bg-blue-700 transition-colors flex items-center gap-2">
                       <span class="material-icons-outlined text-[16px]">upload_file</span> Submit Work
                     </button>`
                   : '<span class="bg-green-100 border border-green-200 text-green-700 px-3 py-1 rounded shadow-sm text-sm font-bold flex items-center gap-1"><span class="material-icons-outlined text-[16px]">check_circle</span> Completed</span>'
                 }
             </div>
         `).join('');
         document.getElementById('assign-container').innerHTML = html || '<p class="text-gray-500 text-center py-6">🎉 No pending assignments! You\'re all caught up.</p>';
     });
}

function submitAssignment(id, title) {
    const el = document.getElementById(`assignment-${id}`);
    if (el) {
        // Show submitting state
        const btn = el.querySelector('button');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<span class="material-icons-outlined text-[16px] animate-spin">sync</span> Submitting...';
        }
    }
    
    fetch(`/api/portal/assignments/${id}/submit`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'}
    }).then(r => r.json()).then(res => {
        if (res.success) {
            showToast(`✅ "${title}" submitted successfully!`, 'success');
            loadAssignments(); // Reload the list
        } else {
            showToast('❌ Failed to submit. Please try again.', 'error');
        }
    }).catch(() => {
        showToast('❌ Network error. Please try again.', 'error');
    });
}

// ─── EXAMS ───────────────────────────────────────────────────
function loadExams() {
    fetch('/api/portal/exams').then(r => r.json()).then(data => {
        if (!data.success) return;
        const d = data.data;

        let upcomingHtml = d.upcoming.map(e => `
            <div class="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <h4 class="text-xl font-bold text-gray-800">${e.subject}</h4>
                        <p class="text-sm text-gray-500 font-medium">${e.type}</p>
                    </div>
                    <span class="bg-red-50 text-red-600 px-3 py-1 rounded-full text-xs font-bold animate-pulse">${e.days_left} days left</span>
                </div>
                <div class="space-y-2 text-sm text-gray-600 mb-4">
                    <div class="flex items-center gap-2"><span class="material-icons-outlined text-[16px] text-gray-400">calendar_today</span> ${e.date}</div>
                    <div class="flex items-center gap-2"><span class="material-icons-outlined text-[16px] text-gray-400">schedule</span> ${e.time}</div>
                    <div class="flex items-center gap-2"><span class="material-icons-outlined text-[16px] text-gray-400">room</span> ${e.room}</div>
                </div>
                <div class="bg-gray-50 rounded-lg p-3">
                    <p class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Syllabus</p>
                    ${e.syllabus.map(s => `<p class="text-sm text-gray-700">• ${s}</p>`).join('')}
                </div>
                <button onclick="openAITutor('${e.subject}')" class="w-full mt-4 bg-indigo-50 text-indigo-700 py-2 rounded-lg font-semibold text-sm hover:bg-indigo-100 transition-colors flex items-center justify-center gap-2">
                    <span class="material-icons-outlined text-[16px]">smart_toy</span> AI Study Plan for This Exam
                </button>
            </div>
        `).join('');

        let mockHtml = d.mock_tests.map(m => `
            <button onclick="startMockTest('${m.subject}')" class="w-full text-left p-4 hover:bg-gray-50 border border-gray-100 rounded-xl flex items-center justify-between group transition-colors">
                <div>
                    <p class="font-semibold text-gray-800">${m.subject}</p>
                    <p class="text-xs text-gray-500">${m.questions} questions • ${m.duration}</p>
                </div>
                <div class="flex items-center gap-3">
                    <span class="text-xs font-bold px-2 py-1 rounded-full ${m.difficulty === 'Easy' ? 'bg-green-100 text-green-700' : m.difficulty === 'Medium' ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}">${m.difficulty}</span>
                    <span class="material-icons-outlined text-gray-400 group-hover:text-blue-500 transition-colors">play_arrow</span>
                </div>
            </button>
        `).join('');

        let pastHtml = d.past_results.map(r => `
            <div class="flex items-center justify-between p-3 border border-gray-100 rounded-xl">
                <div>
                    <p class="font-semibold text-gray-800">${r.subject}</p>
                    <p class="text-xs text-gray-500">${r.type}</p>
                </div>
                <div class="flex items-center gap-3">
                    <div class="w-20 bg-gray-100 rounded-full h-2">
                        <div class="bg-gradient-to-r ${r.score >= 80 ? 'from-green-400 to-emerald-500' : r.score >= 60 ? 'from-yellow-400 to-amber-500' : 'from-red-400 to-rose-500'} h-2 rounded-full" style="width: ${r.score}%"></div>
                    </div>
                    <span class="font-bold text-gray-700">${r.score}/${r.max_score}</span>
                    <span class="text-xs font-bold px-2 py-1 rounded-full ${r.grade.startsWith('A') ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}">${r.grade}</span>
                </div>
            </div>
        `).join('');

        let html = `
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                ${upcomingHtml}
            </div>
            
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div class="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                    <h3 class="font-bold text-xl text-gray-800 mb-4 flex items-center gap-2">
                        <span class="material-icons-outlined text-indigo-500">quiz</span> Mock Tests
                    </h3>
                    <div class="space-y-3">${mockHtml}</div>
                </div>
                
                <div class="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                    <h3 class="font-bold text-xl text-gray-800 mb-4 flex items-center gap-2">
                        <span class="material-icons-outlined text-green-500">assessment</span> Past Results
                    </h3>
                    <div class="space-y-3">${pastHtml}</div>
                </div>
            </div>
        `;
        document.getElementById('sec-exams').innerHTML = html;
    });
}

let currentTestQuestions = [];

function startMockTest(subject) {
    const modal = document.getElementById('mock-test-modal');
    const title = document.getElementById('mock-test-title');
    const loading = document.getElementById('mock-test-loading');
    const qContainer = document.getElementById('mock-test-questions');
    const footer = document.getElementById('mock-test-footer');
    const results = document.getElementById('mock-test-results');
    
    // Reset state
    modal.classList.remove('hidden');
    title.innerText = `Mock Test: ${subject}`;
    loading.classList.remove('hidden');
    qContainer.classList.add('hidden');
    qContainer.innerHTML = '';
    footer.classList.add('hidden');
    results.classList.add('hidden');
    currentTestQuestions = [];
    
    // Fetch questions
    fetch('/api/portal/mock_test/generate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ subject: subject })
    }).then(r => r.json()).then(res => {
        if (!res.success) return;
        currentTestQuestions = res.data.questions;
        
        // Render questions
        let html = '';
        currentTestQuestions.forEach((q, i) => {
            html += `
                <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 mb-4" id="q-container-${i}">
                    <h3 class="font-bold text-lg text-gray-800 mb-4">Q${i + 1}. ${q.question}</h3>
                    <div class="space-y-3">
                        ${q.options.map((opt, optIdx) => `
                            <label class="flex items-center gap-3 p-3 rounded-lg border border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors" id="label-q${i}-opt${optIdx}">
                                <input type="radio" name="q${i}" value="${optIdx}" class="w-5 h-5 text-indigo-600 focus:ring-indigo-500">
                                <span class="font-medium text-gray-700">${opt}</span>
                            </label>
                        `).join('')}
                    </div>
                </div>
            `;
        });
        
        qContainer.innerHTML = html;
        loading.classList.add('hidden');
        qContainer.classList.remove('hidden');
        footer.classList.remove('hidden');
        footer.style.display = 'flex';
    }).catch(err => {
        showToast('❌ Failed to generate test. Try again.', 'error');
        closeMockTest();
    });
}

function closeMockTest() {
    const modal = document.getElementById('mock-test-modal');
    modal.classList.add('hidden');
}

function submitMockTest() {
    if (currentTestQuestions.length === 0) return;
    
    let score = 0;
    
    currentTestQuestions.forEach((q, i) => {
        const selected = document.querySelector(`input[name="q${i}"]:checked`);
        
        // Disable inputs
        document.querySelectorAll(`input[name="q${i}"]`).forEach(el => el.disabled = true);
        
        if (selected) {
            const val = parseInt(selected.value);
            if (val === q.correct_index) {
                score++;
                document.getElementById(`label-q${i}-opt${val}`).classList.add('bg-green-50', 'border-green-200');
            } else {
                document.getElementById(`label-q${i}-opt${val}`).classList.add('bg-red-50', 'border-red-200');
                document.getElementById(`label-q${i}-opt${q.correct_index}`).classList.add('bg-green-50', 'border-green-200');
            }
        } else {
            // Highlight correct one if missed
            document.getElementById(`label-q${i}-opt${q.correct_index}`).classList.add('bg-green-50', 'border-green-200');
        }
    });
    
    const pct = Math.round((score / currentTestQuestions.length) * 100);
    const results = document.getElementById('mock-test-results');
    const footer = document.getElementById('mock-test-footer');
    
    footer.classList.add('hidden');
    footer.style.display = 'none';
    
    results.innerHTML = `
        <div class="inline-block p-8 bg-white rounded-3xl shadow-sm border border-gray-100">
            <span class="material-icons-outlined text-6xl ${pct >= 70 ? 'text-green-500' : 'text-yellow-500'} mb-4">workspace_premium</span>
            <h2 class="text-3xl font-bold text-gray-800 mb-2">Test Completed!</h2>
            <p class="text-gray-500 mb-6">You scored <span class="font-bold text-indigo-600">${score}</span> out of ${currentTestQuestions.length}</p>
            <div class="w-full bg-gray-100 rounded-full h-4 mb-6">
                <div class="bg-gradient-to-r from-blue-500 to-indigo-500 h-4 rounded-full transition-all" style="width: ${pct}%"></div>
            </div>
            <button onclick="closeMockTest()" class="px-8 py-3 bg-gray-900 text-white font-bold rounded-xl shadow-lg hover:bg-gray-800 transition-colors">Close</button>
        </div>
    `;
    results.classList.remove('hidden');
}

// ─── ACHIEVEMENTS ────────────────────────────────────────────
function loadAchievements() {
    fetch('/api/portal/achievements').then(r => r.json()).then(data => {
        if (!data.success) return;
        const d = data.data;
        const stats = d.stats;

        const colorMap = {
            yellow: {bg: 'bg-yellow-100', text: 'text-yellow-600'},
            indigo: {bg: 'bg-indigo-100', text: 'text-indigo-600'},
            amber: {bg: 'bg-amber-100', text: 'text-amber-600'},
            blue: {bg: 'bg-blue-100', text: 'text-blue-600'},
            green: {bg: 'bg-green-100', text: 'text-green-600'},
            red: {bg: 'bg-red-100', text: 'text-red-600'},
            purple: {bg: 'bg-purple-100', text: 'text-purple-600'},
            orange: {bg: 'bg-orange-100', text: 'text-orange-600'},
        };

        let achievementsHtml = d.achievements.map(a => {
            const c = colorMap[a.color] || colorMap.blue;
            return `
                <div class="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm text-center hover:shadow-md transition-shadow relative ${!a.earned ? 'opacity-50 grayscale' : ''}">
                    ${!a.earned ? '<div class="absolute top-3 right-3"><span class="material-icons-outlined text-gray-400 text-[18px]">lock</span></div>' : ''}
                    <div class="w-16 h-16 mx-auto ${c.bg} ${c.text} rounded-full flex items-center justify-center mb-3">
                        <span class="material-icons-outlined text-[32px]">${a.icon}</span>
                    </div>
                    <h4 class="font-bold text-gray-800">${a.title}</h4>
                    <p class="text-xs text-gray-500 mt-1">${a.desc}</p>
                    ${a.earned ? '<span class="inline-block mt-2 text-[10px] bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-bold">✓ Earned</span>' : '<span class="inline-block mt-2 text-[10px] bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full font-bold">🔒 Locked</span>'}
                </div>
            `;
        }).join('');

        let html = `
            <!-- Stats Bar -->
            <div class="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-2xl p-6 text-white shadow-lg mb-6">
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                    <div>
                        <p class="text-indigo-200 text-xs uppercase font-semibold">Badges Earned</p>
                        <p class="text-3xl font-extrabold">${stats.total_earned}/${stats.total_available}</p>
                    </div>
                    <div>
                        <p class="text-indigo-200 text-xs uppercase font-semibold">XP Points</p>
                        <p class="text-3xl font-extrabold">${stats.xp_points}</p>
                    </div>
                    <div>
                        <p class="text-indigo-200 text-xs uppercase font-semibold">Level</p>
                        <p class="text-3xl font-extrabold">${stats.level}</p>
                    </div>
                    <div>
                        <p class="text-indigo-200 text-xs uppercase font-semibold">Completion</p>
                        <p class="text-3xl font-extrabold">${Math.round(stats.total_earned / stats.total_available * 100)}%</p>
                    </div>
                </div>
            </div>
            
            <!-- Achievement Grid -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                ${achievementsHtml}
            </div>
        `;
        document.getElementById('sec-achievements').innerHTML = html;
    });
}

// ─── ANALYTICS ───────────────────────────────────────────────
function loadAnalytics() {
    document.getElementById('sec-analytics').innerHTML = `<div class="flex flex-col items-center justify-center py-12 text-gray-500"><span class="material-icons-outlined text-4xl animate-pulse text-purple-400 mb-2">auto_awesome</span><p>AI is generating learning insights...</p></div>`;
    fetch('/api/portal/analytics').then(r => r.json()).then(data => {
        if (!data.success) return;
        const d = data.data;

        let subjectBars = Object.entries(d.subject_time).map(([subject, pct]) => `
            <div class="flex items-center gap-3 mb-3">
                <span class="text-sm font-medium text-gray-700 w-24">${subject}</span>
                <div class="flex-1 bg-gray-100 rounded-full h-3">
                    <div class="bg-gradient-to-r from-blue-500 to-indigo-500 h-3 rounded-full transition-all" style="width: ${pct}%"></div>
                </div>
                <span class="text-sm font-bold text-gray-600 w-10 text-right">${pct}%</span>
            </div>
        `).join('');

        let weeklyBars = d.weekly_progress.map(w => `
            <div class="text-center">
                <div class="h-32 flex items-end justify-center mb-2">
                    <div class="w-10 bg-gradient-to-t from-indigo-500 to-blue-400 rounded-t-lg transition-all hover:from-indigo-600 hover:to-blue-500" style="height: ${w.score}%"></div>
                </div>
                <p class="text-xs text-gray-500 font-medium">${w.week}</p>
                <p class="text-xs font-bold text-gray-700">${w.score}</p>
            </div>
        `).join('');

        let tipsHtml = d.ai_tips.map(tip => `
            <div class="flex items-start gap-3 bg-blue-50 p-3 rounded-lg border border-blue-100">
                <span class="material-icons-outlined text-blue-500 text-[18px] mt-0.5">lightbulb</span>
                <p class="text-sm font-medium text-blue-900">${tip}</p>
            </div>
        `).join('');

        let html = `
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Focus Score -->
                <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                    <h3 class="text-lg font-bold text-gray-800 mb-4">Focus Score</h3>
                    <div class="relative w-32 h-32 mx-auto flex items-center justify-center mb-4">
                        <svg class="w-full h-full transform -rotate-90">
                            <circle cx="64" cy="64" r="56" class="stroke-gray-100" stroke-width="10" fill="none"></circle>
                            <circle cx="64" cy="64" r="56" class="${d.focus_score >= 80 ? 'stroke-green-500' : d.focus_score >= 60 ? 'stroke-yellow-500' : 'stroke-red-500'}" stroke-width="10" fill="none" stroke-dasharray="351.9" stroke-dashoffset="${351.9 - (351.9 * d.focus_score / 100)}" stroke-linecap="round"></circle>
                        </svg>
                        <div class="absolute text-2xl font-extrabold text-gray-800">${d.focus_score}</div>
                    </div>
                    <p class="text-center text-sm text-gray-600">out of 100</p>
                    <div class="mt-4 space-y-2 text-sm">
                        <div class="flex justify-between text-gray-600"><span>Peak Hours</span><span class="font-bold">${d.study_pattern.peak_hours}</span></div>
                        <div class="flex justify-between text-gray-600"><span>Daily Avg</span><span class="font-bold">${d.study_pattern.avg_daily_hours}h</span></div>
                        <div class="flex justify-between text-gray-600"><span>Best Day</span><span class="font-bold">${d.study_pattern.most_productive_day}</span></div>
                        <div class="flex justify-between text-gray-600"><span>Streak</span><span class="font-bold">${d.study_pattern.streak_days} days 🔥</span></div>
                    </div>
                </div>

                <!-- Subject Distribution -->
                <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                    <h3 class="text-lg font-bold text-gray-800 mb-4">Time Distribution by Subject</h3>
                    ${subjectBars}
                </div>

                <!-- Weekly Progress -->
                <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                    <h3 class="text-lg font-bold text-gray-800 mb-4">Weekly Progress</h3>
                    <div class="flex justify-around items-end h-44">
                        ${weeklyBars}
                    </div>
                </div>
            </div>

            <!-- AI Tips -->
            <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 mt-6">
                <h3 class="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                    <span class="material-icons-outlined text-purple-500">auto_awesome</span> AI Learning Insights
                </h3>
                <div class="space-y-3">
                    ${tipsHtml}
                </div>
            </div>
        `;
        document.getElementById('sec-analytics').innerHTML = html;
    });
}

// ─── AI TUTOR ────────────────────────────────────────────────
// In-memory chat history for conversation context
const chatHistory = [];

function toggleChatbot() {
    const cb = document.getElementById('chatbot');
    cb.classList.toggle('open');
}

// Shortcut: pre-fill and send a message (used by quick-action buttons)
function quickAskTutor(text) {
    const input = document.getElementById('chat-input');
    input.value = text;
    sendMsg();
}

function sendMsg() {
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if(!msg) return;
    
    const container = document.getElementById('chat-messages');
    
    // Append user message
    container.innerHTML += `
        <div class="flex justify-end">
            <div class="bg-slate-800 text-white p-3 rounded-2xl rounded-tr-sm text-sm max-w-[85%] shadow-sm">
                ${escapeHtml(msg)}
            </div>
        </div>
    `;
    input.value = '';
    
    // Track in history
    chatHistory.push({ role: 'user', content: msg });
    
    // Show typing indicator
    const typingId = 'typing-' + Date.now();
    container.innerHTML += `
        <div class="flex justify-start" id="${typingId}">
            <div class="bg-blue-100/50 text-blue-800 p-3 rounded-2xl rounded-tl-sm text-sm inline-block max-w-[85%] border border-blue-100">
                <div class="flex gap-1 items-center">
                    <div class="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style="animation-delay: 0ms"></div>
                    <div class="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style="animation-delay: 150ms"></div>
                    <div class="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style="animation-delay: 300ms"></div>
                </div>
            </div>
        </div>
    `;
    container.scrollTop = container.scrollHeight;
    
    // Fetch AI Tutor response (pass history for context)
    fetch('/api/portal/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ message: msg, history: chatHistory.slice(-10) })
    }).then(r=>r.json()).then(res => {
        // Remove typing indicator
        const typingEl = document.getElementById(typingId);
        if (typingEl) typingEl.remove();
        
        if(res.success) {
            const rawText = res.data.message;
            
            // Track assistant reply in history
            chatHistory.push({ role: 'assistant', content: rawText });
            
            // Format: markdown-style bold, newlines, and simple table detection
            let formatted = rawText
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/\n/g, '<br>');
            
            container.innerHTML += `
                <div class="flex justify-start">
                    <div class="bg-blue-100/50 text-blue-800 p-3 rounded-2xl rounded-tl-sm text-sm inline-block max-w-[85%] border border-blue-100 leading-relaxed">
                        ${formatted}
                    </div>
                </div>
            `;
            container.scrollTop = container.scrollHeight;
        }
    }).catch(() => {
        const typingEl = document.getElementById(typingId);
        if (typingEl) typingEl.remove();
        container.innerHTML += `
            <div class="flex justify-start">
                <div class="bg-red-100/50 text-red-800 p-3 rounded-2xl rounded-tl-sm text-sm inline-block max-w-[85%] border border-red-100">
                    Sorry, I'm having trouble connecting. Please try again!
                </div>
            </div>
        `;
        container.scrollTop = container.scrollHeight;
    });
}


function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ─── TOAST NOTIFICATION SYSTEM ───────────────────────────────
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    const bgColor = type === 'success' ? 'bg-green-600' : type === 'error' ? 'bg-red-600' : 'bg-gray-800';
    
    toast.className = `${bgColor} text-white px-5 py-3 rounded-xl shadow-2xl text-sm font-medium flex items-center gap-2 transform translate-x-full transition-transform duration-300`;
    toast.innerHTML = message;
    
    container.appendChild(toast);
    
    // Animate in
    requestAnimationFrame(() => {
        toast.classList.remove('translate-x-full');
        toast.classList.add('translate-x-0');
    });
    
    // Auto remove
    setTimeout(() => {
        toast.classList.remove('translate-x-0');
        toast.classList.add('translate-x-full');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'fixed top-20 right-6 z-[100] space-y-2';
    document.body.appendChild(container);
    return container;
}
