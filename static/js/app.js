document.addEventListener('DOMContentLoaded', () => {
    console.log("EduSync App Initialized.");

    // Navigation setup based on sidebar text contents (a bit hacky since no IDs provided)
    document.querySelectorAll('div, button, a, span').forEach(el => {
        const text = el.innerText?.trim();
        if(!text) return;
        
        // Find sidebar items looking like nav
        if(el.closest('[class*="bg-surface"]') || el.closest('aside') || el.closest('nav')) {
            el.addEventListener('click', (e) => {
                if(text === 'Dashboard' && !el.closest('form')) window.location.href = '/dashboard';
                else if(text === 'Analytics') window.location.href = '/analytics';
                else if(text === 'Attendance') window.location.href = '/attendance';
                else if(text === 'Students' || text === 'Directory') window.location.href = '/students';
                else if(text === 'Timetable') window.location.href = '/timetable';
                else if(text === 'Settings') window.location.href = '/admin';
                else if(text === 'Logout') window.location.href = '/logout';
            });
        }
    });

    // Dashboard specific
    if(window.location.pathname === '/dashboard') {
        fetchData('/api/dashboard/stats', populateStats);
        fetchData('/api/dashboard/activity-feed', populateActivityFeed);
    }
    
    // Admin specific
    if(window.location.pathname === '/admin') {
        fetchData('/api/admin/stats', populateStats);
        
        // Handle bulk import
        const fileInput = document.querySelector('input[type="file"]');
        if(fileInput) {
            fileInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if(file) {
                    const formData = new FormData();
                    formData.append('file', file);
                    fetch('/api/admin/import', { method: 'POST', body: formData })
                        .then(r => r.json())
                        .then(res => {
                            if(res.success) alert(`Imported ${res.data.success_count} students with ${res.data.error_count} errors.`);
                            else alert("Import failed: " + res.error);
                        });
                }
            });
        }
    }
    
    // Attendance Specific (QR Gen)
    if(window.location.pathname === '/attendance') {
        const genBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Generate') || b.innerText.includes('QR'));
        if(genBtn) {
            genBtn.addEventListener('click', () => {
                fetch('/api/attendance/qr/generate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({class_id: '12A'})
                }).then(r => r.json()).then(res => {
                    if(res.success) {
                        // Find a placeholder img and set it
                        const img = document.querySelector('img[alt="QR Code"]') || document.querySelector('.qr-container img');
                        if(img) img.src = res.data.qr_image_url;
                        alert("Generated new QR code valid for " + res.data.expires_in + " seconds.");
                    }
                });
            });
        }
    }
});

// Helper fetch wrapper
function fetchData(url, callback) {
    fetch(url)
        .then(res => res.json())
        .then(data => {
            if(data.success) {
                callback(data.data);
            }
        }).catch(err => console.error("Error fetching", url, err));
}

function populateStats(data) {
    // Very naive population: try to find number strings in the DOM and replace them
    // Real implementation would use data-* attributes or IDs
    console.log("Stats loaded:", data);
}

function populateActivityFeed(data) {
    console.log("Activity feed loaded:", data);
}
