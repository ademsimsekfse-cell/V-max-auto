/* ═══════════════════════════════════════════════════════════════════════════
   V-MAX SMART ENGINE — Intelligent Auto Service Management
   ═══════════════════════════════════════════════════════════════════════════ */
'use strict';

const VMaxSmart = {

  /* ── Initialization ────────────────────────────────────────────────────── */
  init() {
    this.initDarkMode();
    this.initLiveClock();
    this.initGlobalSearch();
    this.initNotifications();
    this.initCountUp();
    this.initDiagnostics();
    this.initCatalogAutocomplete();
    this.initToasts();
    this.loadAlerts();
    console.log('%c V-MAX SMART ENGINE v2.0 — ONLINE ',
      'background:#1a3a5c;color:#f39c12;font-weight:bold;font-size:14px;padding:4px 8px;border-radius:4px');
  },

  /* ── Dark Mode ─────────────────────────────────────────────────────────── */
  initDarkMode() {
    const saved = localStorage.getItem('vmax-theme') || 'light';
    document.documentElement.setAttribute('data-theme', saved);
    this.updateDarkToggleIcon(saved);
  },

  toggleDarkMode() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('vmax-theme', next);
    this.updateDarkToggleIcon(next);
    this.showToast(next === 'dark' ? '🌙 Gece modu aktif' : '☀️ Gündüz modu aktif', 'info');
  },

  updateDarkToggleIcon(theme) {
    const btn = document.getElementById('dark-toggle');
    if (btn) btn.innerHTML = theme === 'dark'
      ? '<i class="bi bi-sun-fill"></i>'
      : '<i class="bi bi-moon-fill"></i>';
  },

  /* ── Live Clock ────────────────────────────────────────────────────────── */
  initLiveClock() {
    const el = document.getElementById('live-clock');
    if (!el) return;
    const days = ['Paz','Pzt','Sal','Çar','Per','Cum','Cmt'];
    const update = () => {
      const now = new Date();
      el.textContent = `${days[now.getDay()]} ${now.toLocaleDateString('tr-TR')} ${now.toLocaleTimeString('tr-TR')}`;
    };
    update();
    setInterval(update, 1000);
  },

  /* ── Global Search ─────────────────────────────────────────────────────── */
  initGlobalSearch() {
    const input = document.getElementById('global-search');
    const dropdown = document.getElementById('search-dropdown');
    if (!input || !dropdown) return;

    let searchTimer;
    input.addEventListener('input', () => {
      clearTimeout(searchTimer);
      const q = input.value.trim();
      if (q.length < 2) { dropdown.classList.remove('show'); return; }
      searchTimer = setTimeout(() => this.performSearch(q), 300);
    });

    input.addEventListener('focus', () => {
      if (input.value.length >= 2) dropdown.classList.add('show');
    });

    document.addEventListener('click', (e) => {
      if (!e.target.closest('.global-search-wrapper')) dropdown.classList.remove('show');
    });

    input.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') { dropdown.classList.remove('show'); input.blur(); }
    });
  },

  async performSearch(q) {
    const dropdown = document.getElementById('search-dropdown');
    if (!dropdown) return;
    dropdown.innerHTML = '<div class="p-3 text-center text-muted"><div class="spinner-border spinner-border-sm me-2"></div>Aranıyor...</div>';
    dropdown.classList.add('show');
    try {
      const res = await fetch(`/api/smart/search?q=${encodeURIComponent(q)}`);
      const data = await res.json();
      if (data.results.length === 0) {
        dropdown.innerHTML = '<div class="p-3 text-center text-muted"><i class="bi bi-search me-2"></i>Sonuç bulunamadı</div>';
        return;
      }
      const tc = { vehicle: '#0d6efd', customer: '#198754', service: '#fd7e14' };
      const tn = { vehicle: 'Araç', customer: 'Müşteri', service: 'Servis' };
      dropdown.innerHTML = data.results.map(r => `
        <a href="${r.link}" class="search-result-item">
          <div class="search-result-icon" style="background:${tc[r.type]}18;color:${tc[r.type]}">
            <i class="bi bi-${r.icon}"></i>
          </div>
          <div class="flex-grow-1 min-width-0">
            <div class="fw-semibold text-truncate" style="font-size:0.88rem">${r.title}</div>
            <div class="text-muted text-truncate" style="font-size:0.75rem">${r.subtitle}</div>
          </div>
          <span class="badge ms-2" style="background:${tc[r.type]}22;color:${tc[r.type]};font-size:0.65rem">${tn[r.type]}</span>
        </a>
      `).join('');
    } catch(e) {
      dropdown.innerHTML = '<div class="p-3 text-center text-danger"><i class="bi bi-exclamation-triangle me-2"></i>Hata oluştu</div>';
    }
  },

  /* ── Smart Alerts / Notifications ─────────────────────────────────────── */
  async loadAlerts() {
    try {
      const res = await fetch('/api/smart/alerts');
      const data = await res.json();
      const badge = document.getElementById('notification-badge');
      if (badge) {
        if (data.count > 0) {
          badge.textContent = data.count > 9 ? '9+' : data.count;
          badge.style.display = 'flex';
        } else {
          badge.style.display = 'none';
        }
      }
      const alertsList = document.getElementById('alerts-list');
      if (alertsList) {
        const typeIcon = { warning: 'exclamation-triangle-fill', danger: 'x-circle-fill', info: 'info-circle-fill' };
        if (data.alerts.length > 0) {
          alertsList.innerHTML = data.alerts.slice(0, 8).map(a => `
            <a href="${a.link}" class="alert-item ${a.type}">
              <div class="alert-item-icon"><i class="bi bi-${typeIcon[a.type] || 'bell-fill'}"></i></div>
              <div>
                <div style="font-size:0.82rem;font-weight:600">${a.title}</div>
                <div style="font-size:0.75rem;opacity:0.7">${a.message}</div>
              </div>
            </a>
          `).join('');
        } else {
          alertsList.innerHTML = '<div class="p-4 text-center text-muted"><i class="bi bi-check-circle-fill text-success me-2"></i>Uyarı yok, her şey yolunda!</div>';
        }
      }
      // Show critical alerts as toasts
      data.alerts.filter(a => a.priority >= 3).slice(0, 2).forEach((a, i) => {
        setTimeout(() => this.showToast(a.title, a.type, a.message), i * 1200);
      });
    } catch(e) {
      console.warn('Alerts load failed:', e);
    }
  },

  initNotifications() {
    setInterval(() => this.loadAlerts(), 60000);
  },

  /* ── Count-Up Animation ────────────────────────────────────────────────── */
  initCountUp() {
    const els = document.querySelectorAll('[data-countup]');
    if (!els.length) return;
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          this.animateCountUp(entry.target);
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.3 });
    els.forEach(el => observer.observe(el));
  },

  animateCountUp(el) {
    const target = parseFloat(el.getAttribute('data-countup')) || 0;
    const prefix = el.getAttribute('data-prefix') || '';
    const suffix = el.getAttribute('data-suffix') || '';
    const decimals = parseInt(el.getAttribute('data-decimals') || '0');
    const duration = 1500;
    const start = performance.now();
    const easeOut = t => 1 - Math.pow(1 - t, 3);
    const update = (now) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const current = target * easeOut(progress);
      el.textContent = prefix + current.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, '.') + suffix;
      if (progress < 1) requestAnimationFrame(update);
    };
    requestAnimationFrame(update);
  },

  /* ── Smart Diagnostic Engine ───────────────────────────────────────────── */
  initDiagnostics() {
    const textarea = document.getElementById('complaint');
    if (!textarea) return;
    const panel = document.getElementById('diagnostic-panel');
    if (!panel) return;
    let diagTimer;
    textarea.addEventListener('input', () => {
      clearTimeout(diagTimer);
      const val = textarea.value.trim();
      if (val.length < 5) { panel.style.display = 'none'; return; }
      diagTimer = setTimeout(() => this.fetchDiagnostics(val), 700);
    });
  },

  async fetchDiagnostics(complaint) {
    const panel = document.getElementById('diagnostic-panel');
    if (!panel) return;
    try {
      const res = await fetch('/api/smart/diagnostics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ complaint })
      });
      const data = await res.json();
      if (!data.suggestions.length) { panel.style.display = 'none'; return; }
      panel.innerHTML = `
        <div class="d-flex align-items-center gap-2 mb-2">
          <i class="bi bi-cpu-fill text-primary"></i>
          <span class="fw-semibold" style="font-size:0.85rem">SMART TANI — Olası İşlemler</span>
          <span class="badge bg-primary bg-opacity-10 text-primary" style="font-size:0.7rem">${data.count} öneri</span>
        </div>
        <div class="d-flex flex-wrap gap-1">
          ${data.suggestions.map(s => `
            <span class="diagnostic-chip"
              onclick="VMaxSmart.addDiagnosticChip(this, '${s.suggestion.replace(/'/g,"\\'")}')">
              <i class="bi bi-plus-circle"></i>
              ${s.suggestion}
              ${s.min_cost ? `<span class="cost-hint">₺${s.min_cost}–${s.max_cost}</span>` : ''}
            </span>
          `).join('')}
        </div>
      `;
      panel.style.display = 'block';
      panel.style.animation = 'fadeInUp 0.3s ease';
    } catch(e) {
      panel.style.display = 'none';
    }
  },

  addDiagnosticChip(chip, text) {
    chip.classList.toggle('selected');
    const taskArea = document.getElementById('tasks_description');
    if (taskArea && chip.classList.contains('selected')) {
      taskArea.value = taskArea.value ? taskArea.value + '\n' + text : text;
    }
  },

  /* ── Catalog Autocomplete ──────────────────────────────────────────────── */
  initCatalogAutocomplete() {
    document.querySelectorAll('.catalog-autocomplete').forEach(input => {
      let dropdown = null;
      let timer;
      const createDropdown = () => {
        dropdown = document.createElement('div');
        dropdown.className = 'search-dropdown';
        dropdown.style.minWidth = '280px';
        input.parentElement.style.position = 'relative';
        input.parentElement.appendChild(dropdown);
        return dropdown;
      };
      input.addEventListener('input', () => {
        clearTimeout(timer);
        const q = input.value.trim();
        if (!dropdown) createDropdown();
        if (!q) { dropdown.classList.remove('show'); return; }
        timer = setTimeout(() => this.fetchCatalog(q, input, dropdown), 200);
      });
      document.addEventListener('click', (e) => {
        if (dropdown && !e.target.closest('.catalog-autocomplete')) dropdown.classList.remove('show');
      });
    });
  },

  async fetchCatalog(q, input, dropdown) {
    try {
      const res = await fetch(`/api/smart/suggestions?q=${encodeURIComponent(q)}`);
      const data = await res.json();
      if (!data.items.length) { dropdown.classList.remove('show'); return; }
      dropdown.innerHTML = data.items.map(item => `
        <div class="search-result-item" style="cursor:pointer"
          onclick="VMaxSmart.selectCatalogItem(this, '${item.name.replace(/'/g,"\\'")}', ${item.price})">
          <div class="search-result-icon"
            style="background:${item.type==='part'?'#fd7e1418':'#0d6efd18'};color:${item.type==='part'?'#fd7e14':'#0d6efd'}">
            <i class="bi bi-${item.type==='part'?'box-seam':'wrench'}"></i>
          </div>
          <div class="flex-grow-1">
            <div style="font-size:0.88rem;font-weight:600">${item.name}</div>
            <div style="font-size:0.75rem;color:var(--text-muted)">₺${item.price} • ${item.type==='part'?'Parça':'Hizmet'}</div>
          </div>
        </div>
      `).join('');
      dropdown.classList.add('show');
    } catch(e) {}
  },

  selectCatalogItem(el, name, price) {
    const dropdown = el.closest('.search-dropdown');
    const input = dropdown ? dropdown.previousElementSibling : null;
    if (input) {
      input.value = name;
      const row = input.closest('tr');
      if (row) {
        const priceInput = row.querySelector('.item-price');
        if (priceInput) {
          priceInput.value = price;
          priceInput.dispatchEvent(new Event('input'));
        }
      }
    }
    if (dropdown) dropdown.classList.remove('show');
  },

  /* ── Dashboard Charts ──────────────────────────────────────────────────── */
  async initDashboardCharts() {
    if (!document.getElementById('revenueChart')) return;
    try {
      const res = await fetch('/api/smart/dashboard');
      const data = await res.json();

      // Update extra stat elements
      const totalRevEl = document.getElementById('total-revenue-stat');
      if (totalRevEl) {
        totalRevEl.setAttribute('data-countup', data.total_revenue);
        totalRevEl.setAttribute('data-decimals', '0');
        totalRevEl.setAttribute('data-prefix', '₺');
        this.animateCountUp(totalRevEl);
      }
      const totalVehEl = document.getElementById('total-vehicles-stat');
      if (totalVehEl) { totalVehEl.setAttribute('data-countup', data.total_vehicles); this.animateCountUp(totalVehEl); }
      const totalCustEl = document.getElementById('total-customers-stat');
      if (totalCustEl) { totalCustEl.setAttribute('data-countup', data.total_customers); this.animateCountUp(totalCustEl); }
      const avgTimeEl = document.getElementById('avg-time-stat');
      if (avgTimeEl) { avgTimeEl.setAttribute('data-countup', data.avg_completion_hours); avgTimeEl.setAttribute('data-decimals', '1'); this.animateCountUp(avgTimeEl); }

      const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      const gridColor = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';
      const textColor = isDark ? '#8b949e' : '#6c757d';

      // Revenue Trend
      const revenueCtx = document.getElementById('revenueChart');
      if (revenueCtx) {
        new Chart(revenueCtx, {
          type: 'line',
          data: {
            labels: data.revenue_chart.labels,
            datasets: [{
              label: 'Gelir (₺)',
              data: data.revenue_chart.data,
              borderColor: '#2e6da4',
              backgroundColor: 'rgba(46,109,164,0.1)',
              borderWidth: 3, fill: true, tension: 0.4,
              pointBackgroundColor: '#2e6da4', pointRadius: 5, pointHoverRadius: 8,
            }]
          },
          options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              x: { grid: { color: gridColor }, ticks: { color: textColor } },
              y: { grid: { color: gridColor }, ticks: { color: textColor, callback: v => '₺' + v.toLocaleString('tr-TR') } }
            }
          }
        });
      }

      // Status Donut
      const statusCtx = document.getElementById('statusChart');
      if (statusCtx) {
        new Chart(statusCtx, {
          type: 'doughnut',
          data: {
            labels: ['Bekliyor', 'İşlemde', 'Tamamlandı', 'Teslim'],
            datasets: [{
              data: [data.status_chart.waiting, data.status_chart.in_progress, data.status_chart.completed, data.status_chart.delivered],
              backgroundColor: ['#ffc107','#0d6efd','#198754','#6c757d'],
              borderWidth: 0, hoverOffset: 6,
            }]
          },
          options: {
            responsive: true, maintainAspectRatio: false, cutout: '70%',
            plugins: { legend: { position: 'bottom', labels: { color: textColor, padding: 16, font: { size: 12 } } } }
          }
        });
      }

      // Unit Performance
      const unitCtx = document.getElementById('unitChart');
      if (unitCtx && data.unit_data.length > 0) {
        new Chart(unitCtx, {
          type: 'bar',
          data: {
            labels: data.unit_data.map(u => u.name),
            datasets: [
              { label: 'Servis Sayısı', data: data.unit_data.map(u => u.count), backgroundColor: 'rgba(46,109,164,0.75)', borderRadius: 6, yAxisID: 'y' },
              { label: 'Gelir (₺)', data: data.unit_data.map(u => u.revenue), backgroundColor: 'rgba(243,156,18,0.75)', borderRadius: 6, yAxisID: 'y1' }
            ]
          },
          options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { labels: { color: textColor } } },
            scales: {
              x: { grid: { display: false }, ticks: { color: textColor } },
              y: { grid: { color: gridColor }, ticks: { color: textColor } },
              y1: { position: 'right', grid: { display: false }, ticks: { color: textColor, callback: v => '₺' + v.toLocaleString('tr-TR') } }
            }
          }
        });
      }

      this.loadKanban();
    } catch(e) {
      console.warn('Dashboard charts error:', e);
    }
  },

  /* ── Kanban Board ──────────────────────────────────────────────────────── */
  async loadKanban() {
    const board = document.getElementById('kanban-board');
    if (!board) return;
    try {
      const res = await fetch('/api/smart/kanban');
      const data = await res.json();
      const cols = [
        { key: 'waiting',     label: '⏳ Bekliyor',    badge: 'warning' },
        { key: 'in_progress', label: '🔧 İşlemde',     badge: 'primary' },
        { key: 'completed',   label: '✅ Tamamlandı',  badge: 'success' },
      ];
      board.innerHTML = cols.map(col => `
        <div class="kanban-column col-${col.key}">
          <div class="kanban-column-header">
            <span>${col.label}</span>
            <span class="badge bg-${col.badge}">${data[col.key].length}</span>
          </div>
          <div class="kanban-column-body">
            ${data[col.key].length === 0
              ? '<div class="text-center text-muted py-4" style="font-size:0.8rem">Kayıt yok</div>'
              : data[col.key].map(card => `
                <div class="kanban-card" onclick="window.location='${card.link}'">
                  <div class="d-flex justify-content-between align-items-start">
                    <span class="plate">${card.plate}</span>
                    <span class="badge bg-secondary bg-opacity-10 text-secondary" style="font-size:0.65rem">${card.record_no}</span>
                  </div>
                  <div class="vehicle-name">${card.vehicle}</div>
                  ${card.complaint ? `<div class="complaint-preview">${card.complaint}</div>` : ''}
                  <div class="meta">
                    <span>${card.unit || ''}</span>
                    <span><i class="bi bi-clock me-1"></i>${card.hours_ago}s önce</span>
                  </div>
                </div>
              `).join('')
            }
          </div>
        </div>
      `).join('');
    } catch(e) {
      console.warn('Kanban load error:', e);
    }
  },

  /* ── Toast Notifications ───────────────────────────────────────────────── */
  initToasts() {
    if (!document.getElementById('toast-container')) {
      const c = document.createElement('div');
      c.id = 'toast-container';
      c.className = 'smart-toast-container';
      document.body.appendChild(c);
    }
  },

  showToast(title, type = 'info', message = '', duration = 4000) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const icons = { success: 'check-circle-fill', warning: 'exclamation-triangle-fill', danger: 'x-circle-fill', info: 'info-circle-fill' };
    const colors = { success: '#198754', warning: '#ffc107', danger: '#dc3545', info: '#0dcaf0' };
    const toast = document.createElement('div');
    toast.className = `smart-toast ${type}`;
    toast.innerHTML = `
      <i class="bi bi-${icons[type]||'info-circle-fill'}" style="color:${colors[type]};font-size:1.2rem;flex-shrink:0"></i>
      <div>
        <div style="font-weight:600;font-size:0.85rem">${title}</div>
        ${message ? `<div style="font-size:0.75rem;opacity:0.75;margin-top:2px">${message}</div>` : ''}
      </div>
      <button onclick="this.closest('.smart-toast').remove()"
        style="background:none;border:none;opacity:0.5;cursor:pointer;font-size:1.1rem;margin-left:auto;line-height:1;padding:0">×</button>
    `;
    container.appendChild(toast);
    setTimeout(() => {
      toast.classList.add('exiting');
      setTimeout(() => toast.remove(), 300);
    }, duration);
  },

  /* ── Vehicle Health ────────────────────────────────────────────────────── */
  async loadVehicleHealth(vehicleId) {
    const panel = document.getElementById('vehicle-health-panel');
    if (!panel || !vehicleId) return;
    try {
      const res = await fetch(`/api/vehicles/${vehicleId}/health`);
      const data = await res.json();
      const colorMap = { success: '#198754', warning: '#ffc107', danger: '#dc3545' };
      const color = colorMap[data.color] || '#198754';
      const circumference = 2 * Math.PI * 34;
      panel.innerHTML = `
        <div class="d-flex align-items-center gap-3 mb-3">
          <div style="position:relative;width:80px;height:80px;flex-shrink:0">
            <svg width="80" height="80" style="transform:rotate(-90deg)">
              <circle cx="40" cy="40" r="34" fill="none" stroke="#e9ecef" stroke-width="8"/>
              <circle cx="40" cy="40" r="34" fill="none" stroke="${color}" stroke-width="8"
                stroke-dasharray="${circumference}" stroke-dashoffset="${circumference*(1-data.score/100)}"
                stroke-linecap="round" style="transition:stroke-dashoffset 1.2s ease"/>
            </svg>
            <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center">
              <div style="font-size:1.3rem;font-weight:900;color:${color};line-height:1">${data.score}</div>
              <div style="font-size:0.55rem;font-weight:600;color:#6c757d">SAĞLIK</div>
            </div>
          </div>
          <div>
            <div class="fw-bold fs-5" style="color:${color}">${data.label}</div>
            <div class="text-muted small">${data.total_services} servis kaydı</div>
          </div>
        </div>
        ${data.warnings.map(w => `
          <div class="alert alert-${w.level} py-2 px-3 mb-2" style="font-size:0.8rem">
            <i class="bi bi-${w.level==='danger'?'exclamation-triangle':w.level==='warning'?'exclamation-circle':'info-circle'} me-1"></i>
            ${w.msg}
          </div>
        `).join('')}
      `;
    } catch(e) {
      panel.innerHTML = '<div class="text-muted small p-2">Sağlık durumu yüklenemedi</div>';
    }
  },

};

/* ── Auto-init ──────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  VMaxSmart.init();
  if (document.getElementById('revenueChart')) {
    VMaxSmart.initDashboardCharts();
  }
});
