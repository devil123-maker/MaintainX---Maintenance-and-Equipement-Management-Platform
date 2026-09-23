(function () {
  'use strict';

  let charts = [];

  function getThemeColors() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    return {
      text: isDark ? '#94a3b8' : '#64748b',
      grid: isDark ? '#334155' : '#e2e8f0',
      primary: isDark ? '#818cf8' : '#4f46e5',
      accent: isDark ? '#22d3ee' : '#06b6d4',
      success: isDark ? '#34d399' : '#10b981',
      warning: isDark ? '#fbbf24' : '#f59e0b',
      danger: isDark ? '#f87171' : '#ef4444',
      purple: isDark ? '#a855f7' : '#9333ea',
    };
  }

  function destroyCharts() {
    charts.forEach((c) => c.destroy());
    charts = [];
  }

  async function initCharts() {
    if (typeof Chart === 'undefined') return;

    destroyCharts();
    const colors = getThemeColors();

    Chart.defaults.color = colors.text;
    Chart.defaults.borderColor = colors.grid;
    Chart.defaults.font.family = "'Inter', system-ui, sans-serif";

    try {
      const response = await fetch('/analytics/?format=json', {
        headers: { 'Accept': 'application/json' }
      });
      if (!response.ok) return;

      const data = await response.json();

      if (data.kpis) {
        const avgResEl = document.getElementById('kpi-avg-resolution');
        const slaEl = document.getElementById('kpi-sla-compliance');
        const totalEl = document.getElementById('kpi-total-requests');
        const completedEl = document.getElementById('kpi-completed-requests');

        if (avgResEl) avgResEl.textContent = data.kpis.avg_resolution;
        if (slaEl) slaEl.textContent = data.kpis.sla_compliance;
        if (totalEl) totalEl.textContent = data.kpis.total_requests;
        if (completedEl) completedEl.textContent = data.kpis.completed_count;
      }

      const lineCtx = document.getElementById('chart-trends');
      if (lineCtx && data.monthly_trends) {
        const labels = data.monthly_trends.map((t) => t.month);
        const opened = data.monthly_trends.map((t) => t.opened);
        const resolved = data.monthly_trends.map((t) => t.resolved);

        charts.push(new Chart(lineCtx, {
          type: 'line',
          data: {
            labels: labels,
            datasets: [{
              label: 'Tickets Opened',
              data: opened,
              borderColor: colors.primary,
              backgroundColor: colors.primary + '20',
              fill: true,
              tension: 0.4,
            }, {
              label: 'Tickets Resolved',
              data: resolved,
              borderColor: colors.success,
              backgroundColor: colors.success + '20',
              fill: true,
              tension: 0.4,
            }],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'bottom' } },
            scales: {
              y: { beginAtZero: true, grid: { color: colors.grid } },
              x: { grid: { display: false } },
            },
          },
        }));
      }

      const pieCtx = document.getElementById('chart-resolution');
      if (pieCtx && data.by_status) {
        const labels = data.by_status.map((s) => s.status.toUpperCase().replace('_', ' '));
        const counts = data.by_status.map((s) => s.count);

        charts.push(new Chart(pieCtx, {
          type: 'doughnut',
          data: {
            labels: labels,
            datasets: [{
              data: counts,
              backgroundColor: [colors.success, colors.warning, colors.primary, colors.danger, colors.accent, colors.purple],
              borderWidth: 0,
            }],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'bottom' } },
          },
        }));
      }

      const teamCtx = document.getElementById('chart-team-performance');
      if (teamCtx && data.by_team) {
        const teamLabels = data.by_team.map((t) => t.name);
        const totalReqs = data.by_team.map((t) => t.total_reqs);
        const completedReqs = data.by_team.map((t) => t.completed_reqs);

        charts.push(new Chart(teamCtx, {
          type: 'bar',
          data: {
            labels: teamLabels.length ? teamLabels : ['No Teams'],
            datasets: [{
              label: 'Total Assigned',
              data: totalReqs.length ? totalReqs : [0],
              backgroundColor: colors.primary,
              borderRadius: 6,
            }, {
              label: 'Completed',
              data: completedReqs.length ? completedReqs : [0],
              backgroundColor: colors.success,
              borderRadius: 6,
            }],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'bottom' } },
            scales: {
              y: { beginAtZero: true, grid: { color: colors.grid } },
              x: { grid: { display: false } },
            },
          },
        }));
      }

      const categoryCtx = document.getElementById('chart-category');
      if (categoryCtx && data.by_category) {
        const catLabels = data.by_category.map((c) => c.category);
        const catCounts = data.by_category.map((c) => c.request_count);

        charts.push(new Chart(categoryCtx, {
          type: 'bar',
          data: {
            labels: catLabels.length ? catLabels : ['General'],
            datasets: [{
              label: 'Maintenance Requests',
              data: catCounts.length ? catCounts : [0],
              backgroundColor: colors.accent,
              borderRadius: 6,
            }],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              y: { beginAtZero: true, grid: { color: colors.grid } },
              x: { grid: { display: false } },
            },
          },
        }));
      }

      const typeCtx = document.getElementById('chart-type');
      if (typeCtx && data.by_type) {
        const typeLabels = data.by_type.map((t) => t.request_type.toUpperCase());
        const typeCounts = data.by_type.map((t) => t.count);

        charts.push(new Chart(typeCtx, {
          type: 'doughnut',
          data: {
            labels: typeLabels,
            datasets: [{
              data: typeCounts,
              backgroundColor: [colors.warning, colors.purple],
              borderWidth: 0,
            }],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'bottom' } },
          },
        }));
      }

    } catch (e) {
      console.error('Failed to initialize reporting charts', e);
    }
  }

  document.addEventListener('DOMContentLoaded', initCharts);
  window.addEventListener('themechange', initCharts);
})();
