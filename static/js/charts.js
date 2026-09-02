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
    };
  }

  function destroyCharts() {
    charts.forEach((c) => c.destroy());
    charts = [];
  }

  function initCharts() {
    if (typeof Chart === 'undefined') return;

    destroyCharts();
    const colors = getThemeColors();

    Chart.defaults.color = colors.text;
    Chart.defaults.borderColor = colors.grid;
    Chart.defaults.font.family = "'Inter', system-ui, sans-serif";

    const lineCtx = document.getElementById('chart-trends');
    if (lineCtx) {
      charts.push(new Chart(lineCtx, {
        type: 'line',
        data: {
          labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
          datasets: [{
            label: 'Tickets Opened',
            data: [42, 58, 45, 72, 65, 80],
            borderColor: colors.primary,
            backgroundColor: colors.primary + '20',
            fill: true,
            tension: 0.4,
          }, {
            label: 'Tickets Resolved',
            data: [38, 52, 48, 68, 70, 75],
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
    if (pieCtx) {
      charts.push(new Chart(pieCtx, {
        type: 'doughnut',
        data: {
          labels: ['Resolved', 'In Progress', 'Open', 'Escalated'],
          datasets: [{
            data: [45, 28, 18, 9],
            backgroundColor: [colors.success, colors.warning, colors.primary, colors.danger],
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

    const barCtx = document.getElementById('chart-efficiency');
    if (barCtx) {
      charts.push(new Chart(barCtx, {
        type: 'bar',
        data: {
          labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
          datasets: [{
            label: 'Avg. Resolution (hrs)',
            data: [4.2, 3.8, 5.1, 3.5, 4.0, 6.2, 5.8],
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
  }

  document.addEventListener('DOMContentLoaded', initCharts);
  window.addEventListener('themechange', initCharts);
})();
