(function () {
  function applyTheme(theme) {
    var root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark-theme');
    } else {
      root.classList.remove('dark-theme');
    }
    localStorage.setItem('coach-theme', theme);
  }

  function parseJsonScript(id) {
    var element = document.getElementById(id);
    if (!element) return null;
    try {
      return JSON.parse(element.textContent);
    } catch (error) {
      return null;
    }
  }

  function getChartTheme() {
    var isDark = document.documentElement.classList.contains('dark-theme');
    return {
      isDark: isDark,
      axis: isDark ? '#94a3b8' : '#64748b',
      axisAccent: isDark ? '#67e8f9' : '#0891b2',
      grid: isDark ? 'rgba(148, 163, 184, 0.10)' : 'rgba(100, 116, 139, 0.14)',
      gridSoft: isDark ? 'rgba(148, 163, 184, 0.045)' : 'rgba(100, 116, 139, 0.08)',
      pointBg: isDark ? '#081526' : '#ffffff',
      tooltipBg: isDark ? 'rgba(2, 6, 23, 0.96)' : 'rgba(255, 255, 255, 0.98)',
      tooltipTitle: isDark ? '#f8fafc' : '#0f172a',
      tooltipBody: isDark ? '#cbd5e1' : '#334155',
      tooltipBorder: isDark ? 'rgba(34, 211, 238, 0.28)' : 'rgba(59, 130, 246, 0.22)',
      glow: isDark ? 'rgba(34, 211, 238, .38)' : 'rgba(59, 130, 246, .20)',
      glowFill: isDark ? 'rgba(34, 211, 238, .16)' : 'rgba(59, 130, 246, .10)'
    };
  }

  function buildLineChart(canvasId, config) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || typeof Chart === 'undefined') return;

    var theme = getChartTheme();
    var ctx = canvas.getContext('2d');
    var gradientPrimary = ctx.createLinearGradient(0, 0, 0, 260);
    gradientPrimary.addColorStop(0, config.fillTop || 'rgba(59,130,246,.28)');
    gradientPrimary.addColorStop(1, config.fillBottom || 'rgba(59,130,246,0)');

    new Chart(canvas, {
      type: 'line',
      data: {
        labels: config.labels,
        datasets: config.datasets.map(function (dataset, index) {
          return {
            label: dataset.label,
            data: dataset.data,
            borderColor: dataset.borderColor,
            backgroundColor: index === 0 ? gradientPrimary : dataset.backgroundColor,
            fill: dataset.fill,
            tension: 0.46,
            borderWidth: dataset.borderWidth || 3,
            pointRadius: 4,
            pointHoverRadius: 7,
            pointHitRadius: 18,
            pointBackgroundColor: dataset.pointBackgroundColor || theme.pointBg,
            pointBorderWidth: 2,
            pointBorderColor: dataset.borderColor,
            pointHoverBackgroundColor: theme.isDark ? '#f8fafc' : '#0f172a',
            pointHoverBorderWidth: 3,
            yAxisID: dataset.yAxisID || 'y',
          };
        })
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
          duration: 1100,
          easing: 'easeOutQuart'
        },
        interaction: {
          mode: 'index',
          intersect: false
        },
        elements: {
          line: {
            capBezierPoints: true
          }
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: theme.tooltipBg,
            titleColor: theme.tooltipTitle,
            bodyColor: theme.tooltipBody,
            borderColor: theme.tooltipBorder,
            borderWidth: 1,
            padding: 15,
            cornerRadius: 16,
            displayColors: true,
            usePointStyle: true,
            caretPadding: 10,
            callbacks: {
              title: function (items) {
                return items.length ? items[0].label + ' oy tahlili' : '';
              },
              label: function (context) {
                var suffix = context.dataset.label.indexOf('%') !== -1 ? '%' : '';
                return ' ' + context.dataset.label + ': ' + context.parsed.y + suffix;
              },
              afterBody: function () {
                return 'Trend: matchday formasi bo\'yicha solishtirilgan';
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            suggestedMax: 100,
            grid: { color: theme.grid, drawBorder: false },
            border: { display: false },
            ticks: {
              color: theme.axis,
              padding: 10,
              callback: function (value) { return value + (config.percentAxis ? '%' : ''); }
            }
          },
          y1: {
            beginAtZero: true,
            position: 'right',
            suggestedMax: 8,
            grid: { drawOnChartArea: false, drawBorder: false },
            border: { display: false },
            ticks: {
              color: theme.axisAccent,
              padding: 10,
              stepSize: 2
            }
          },
          x: {
            grid: { color: theme.gridSoft, drawBorder: false },
            border: { display: false },
            ticks: { color: theme.axis, padding: 10, font: { weight: 700 } }
          }
        }
      }
    });
  }

  var dashboardCharts = parseJsonScript('dashboard-charts-data');
  if (dashboardCharts) {
    if (dashboardCharts.has_performance_data && document.getElementById('performanceChart')) {
      buildLineChart('performanceChart', {
        labels: dashboardCharts.labels,
        percentAxis: true,
        fillTop: 'rgba(59,130,246,.26)',
        fillBottom: 'rgba(59,130,246,0)',
        datasets: [
          {
            label: "Umumiy samaradorlik %",
            data: dashboardCharts.effectiveness,
            borderColor: '#3B82F6',
            backgroundColor: 'rgba(59,130,246,.08)',
            fill: true,
            yAxisID: 'y'
          },
          {
            label: "G'alabalar",
            data: dashboardCharts.wins,
            borderColor: '#22d3ee',
            backgroundColor: 'rgba(34,211,238,.02)',
            fill: false,
            borderWidth: 2,
            yAxisID: 'y1'
          }
        ]
      });
    }

    if (dashboardCharts.has_goals_data && document.getElementById('goalsChart')) {
      const theme = getChartTheme();
      const goalsCanvas = document.getElementById('goalsChart');
      const goalsCtx = goalsCanvas.getContext('2d');
      const goalsGradient = goalsCtx.createLinearGradient(0, 0, 0, 260);
      goalsGradient.addColorStop(0, 'rgba(34, 211, 238, .92)');
      goalsGradient.addColorStop(0.52, 'rgba(59, 130, 246, .74)');
      goalsGradient.addColorStop(1, 'rgba(37, 99, 235, .32)');

      const barGlowPlugin = {
        id: 'barGlow',
        beforeDatasetsDraw: function (chart) {
          const ctx = chart.ctx;
          const meta = chart.getDatasetMeta(0);
          ctx.save();
          meta.data.forEach(function (bar) {
            ctx.shadowColor = theme.glow;
            ctx.shadowBlur = 22;
            ctx.fillStyle = theme.glowFill;
            ctx.fillRect(bar.x - bar.width / 2, bar.y, bar.width, bar.base - bar.y);
          });
          ctx.restore();
        }
      };

      new Chart(goalsCanvas, {
        type: 'bar',
        data: {
          labels: dashboardCharts.labels,
          datasets: [{
            label: 'Gollar',
            data: dashboardCharts.goals,
            backgroundColor: goalsGradient,
            borderColor: 'rgba(125, 211, 252, .72)',
            borderWidth: 1,
            borderRadius: { topLeft: 14, topRight: 14, bottomLeft: 8, bottomRight: 8 },
            hoverBackgroundColor: '#22D3EE',
            maxBarThickness: 42
          }]
        },
        plugins: [barGlowPlugin],
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: {
            duration: 1050,
            easing: 'easeOutQuart'
          },
          interaction: {
            mode: 'index',
            intersect: false
          },
          plugins: {
            legend: { display: false },
            tooltip: {
              backgroundColor: theme.tooltipBg,
              titleColor: theme.tooltipTitle,
              bodyColor: theme.tooltipBody,
              borderColor: theme.tooltipBorder,
              borderWidth: 1,
              padding: 15,
              cornerRadius: 16,
              caretPadding: 10,
              callbacks: {
                title: function (items) {
                  return items.length ? items[0].label + ' hujum outputi' : '';
                },
                label: function (context) {
                  return ' Gollar: ' + context.parsed.y;
                },
                afterBody: function () {
                  return 'Insight: yuqori press va final third kirishlari asosida';
                }
              }
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              grid: { color: theme.grid, drawBorder: false },
              border: { display: false },
              ticks: { color: theme.axis, padding: 10 }
            },
            x: {
              grid: { display: false, drawBorder: false },
              border: { display: false },
              ticks: { color: theme.axis, padding: 10, font: { weight: 700 } }
            }
          }
        }
      });
    }
  }

  var statisticsCharts = parseJsonScript('statistics-charts-data');
  if (statisticsCharts && typeof Chart !== 'undefined') {
    var statsTheme = getChartTheme();
    var attackCanvas = document.getElementById('statisticsAttackChart');
    if (attackCanvas && statisticsCharts.attack && statisticsCharts.attack.labels.length) {
      var attackCtx = attackCanvas.getContext('2d');
      var goalGradient = attackCtx.createLinearGradient(0, 0, 0, 300);
      goalGradient.addColorStop(0, 'rgba(34, 197, 94, .28)');
      goalGradient.addColorStop(1, 'rgba(34, 197, 94, 0)');
      var assistGradient = attackCtx.createLinearGradient(0, 0, 0, 300);
      assistGradient.addColorStop(0, 'rgba(59, 130, 246, .24)');
      assistGradient.addColorStop(1, 'rgba(59, 130, 246, 0)');
      var totalGradient = attackCtx.createLinearGradient(0, 0, 0, 300);
      totalGradient.addColorStop(0, statsTheme.isDark ? 'rgba(34, 211, 238, .20)' : 'rgba(59, 130, 246, .16)');
      totalGradient.addColorStop(1, statsTheme.isDark ? 'rgba(34, 211, 238, .04)' : 'rgba(59, 130, 246, .035)');
      var attackMax = Math.max.apply(null, statisticsCharts.attack.totals.concat(statisticsCharts.attack.goals, statisticsCharts.attack.assists, [4]));
      var guidePlugin = {
        id: 'statisticsHoverGuide',
        afterDatasetsDraw: function (chart) {
          var active = chart.tooltip && chart.tooltip.getActiveElements ? chart.tooltip.getActiveElements() : [];
          if (!active.length) return;
          var ctx = chart.ctx;
          var chartArea = chart.chartArea;
          var x = active[0].element.x;
          ctx.save();
          ctx.beginPath();
          ctx.moveTo(x, chartArea.top + 6);
          ctx.lineTo(x, chartArea.bottom);
          ctx.lineWidth = 1;
          ctx.setLineDash([5, 5]);
          ctx.strokeStyle = statsTheme.isDark ? 'rgba(103, 232, 249, .46)' : 'rgba(37, 99, 235, .30)';
          ctx.stroke();
          ctx.restore();
        }
      };

      new Chart(attackCanvas, {
        type: 'bar',
        data: {
          labels: statisticsCharts.attack.labels,
          datasets: [
            {
              type: 'bar',
              label: 'Umumiy output',
              data: statisticsCharts.attack.totals,
              backgroundColor: totalGradient,
              borderColor: statsTheme.isDark ? 'rgba(103, 232, 249, .24)' : 'rgba(59, 130, 246, .18)',
              borderWidth: 1,
              borderRadius: 12,
              barPercentage: .48,
              categoryPercentage: .64,
              order: 3
            },
            {
              type: 'line',
              label: 'Gollar',
              data: statisticsCharts.attack.goals,
              borderColor: '#22C55E',
              backgroundColor: goalGradient,
              fill: true,
              tension: .42,
              borderWidth: 4,
              pointRadius: 4,
              pointHoverRadius: 8,
              pointHitRadius: 18,
              pointBackgroundColor: statsTheme.pointBg,
              pointBorderColor: '#22C55E',
              pointBorderWidth: 2,
              order: 1
            },
            {
              type: 'line',
              label: 'Golli uzatmalar',
              data: statisticsCharts.attack.assists,
              borderColor: '#3B82F6',
              backgroundColor: assistGradient,
              fill: true,
              tension: .42,
              borderWidth: 4,
              pointRadius: 4,
              pointHoverRadius: 8,
              pointHitRadius: 18,
              pointBackgroundColor: statsTheme.pointBg,
              pointBorderColor: '#3B82F6',
              pointBorderWidth: 2,
              order: 2
            }
          ]
        },
        plugins: [guidePlugin],
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: { duration: 1150, easing: 'easeOutQuart' },
          interaction: { mode: 'index', intersect: false },
          plugins: {
            legend: { display: false },
            tooltip: {
              backgroundColor: statsTheme.tooltipBg,
              titleColor: statsTheme.tooltipTitle,
              bodyColor: statsTheme.tooltipBody,
              borderColor: statsTheme.tooltipBorder,
              borderWidth: 1,
              padding: 15,
              cornerRadius: 16,
              usePointStyle: true,
              caretPadding: 10,
              callbacks: {
                title: function (items) {
                  return items.length ? items[0].label + ' hujum tahlili' : '';
                },
                label: function (context) {
                  return ' ' + context.dataset.label + ': ' + context.parsed.y;
                },
                afterBody: function () {
                  return 'Davr: ' + statisticsCharts.selectedLabel;
                }
              }
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              suggestedMax: attackMax + 2,
              grid: { color: statsTheme.grid, drawBorder: false },
              border: { display: false },
              ticks: { color: statsTheme.axis, padding: 10, precision: 0 }
            },
            x: {
              grid: { color: statsTheme.gridSoft, drawBorder: false },
              border: { display: false },
              ticks: { color: statsTheme.axis, padding: 10, font: { weight: 700 } }
            }
          }
        }
      });
    }

    var resultsCanvas = document.getElementById('statisticsResultsChart');
    if (resultsCanvas && statisticsCharts.results && statisticsCharts.results.total) {
      var resultCtx = resultsCanvas.getContext('2d');
      var segmentGlowPlugin = {
        id: 'statisticsSegmentGlow',
        beforeDatasetDraw: function (chart) {
          chart.ctx.save();
          chart.ctx.shadowColor = statsTheme.isDark ? 'rgba(34, 211, 238, .22)' : 'rgba(59, 130, 246, .18)';
          chart.ctx.shadowBlur = 18;
        },
        afterDatasetDraw: function (chart) {
          chart.ctx.restore();
        }
      };

      new Chart(resultCtx, {
        type: 'doughnut',
        data: {
          labels: statisticsCharts.results.labels,
          datasets: [{
            data: statisticsCharts.results.values,
            backgroundColor: statisticsCharts.results.colors,
            borderColor: statsTheme.isDark ? '#0f172a' : '#f8fafc',
            borderWidth: 4,
            hoverOffset: 10,
            spacing: 2
          }]
        },
        plugins: [segmentGlowPlugin],
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: '67%',
          animation: { animateRotate: true, duration: 1150, easing: 'easeOutQuart' },
          plugins: {
            legend: { display: false },
            tooltip: {
              backgroundColor: statsTheme.tooltipBg,
              titleColor: statsTheme.tooltipTitle,
              bodyColor: statsTheme.tooltipBody,
              borderColor: statsTheme.tooltipBorder,
              borderWidth: 1,
              padding: 14,
              cornerRadius: 16,
              callbacks: {
                label: function (context) {
                  var total = statisticsCharts.results.total || 1;
                  var value = context.parsed || 0;
                  var percent = Math.round((value / total) * 100);
                  return ' ' + context.label + ': ' + value + ' ta (' + percent + '%)';
                },
                afterBody: function () {
                  return "G'alaba foizi: " + statisticsCharts.results.winRate + '%';
                }
              }
            }
          }
        }
      });
    }
  }

  document.querySelectorAll('[data-chart-download]').forEach(function (button) {
    button.addEventListener('click', function () {
      var canvas = document.getElementById(button.getAttribute('data-chart-download'));
      if (!canvas) return;
      var link = document.createElement('a');
      link.download = 'coachpro-statistika.png';
      link.href = canvas.toDataURL('image/png', 1);
      link.click();
    });
  });

  if (window.playerStatsData && document.getElementById('playerStatsChart') && typeof Chart !== 'undefined') {
    new Chart(document.getElementById('playerStatsChart'), {
      type: 'bar',
      data: {
        labels: window.playerStatsData.labels,
        datasets: [
          { label: 'Gollar', data: window.playerStatsData.goals, backgroundColor: '#3b82f6', borderRadius: 10 },
          { label: 'Assistlar', data: window.playerStatsData.assists, backgroundColor: '#06b6d4', borderRadius: 10 }
        ]
      },
      options: {
        plugins: { legend: { position: 'top' } },
        scales: {
          y: { beginAtZero: true, grid: { color: '#edf2f7' }, ticks: { color: '#64748b' } },
          x: { grid: { display: false }, ticks: { color: '#64748b' } }
        }
      }
    });
  }

  var savedTheme = localStorage.getItem('coach-theme');
  if (savedTheme) {
    applyTheme(savedTheme);
  }

  var themeInputs = document.querySelectorAll('input[name="theme"]');
  themeInputs.forEach(function (input) {
    if (savedTheme && input.value === savedTheme) {
      input.checked = true;
    }
    input.addEventListener('change', function () {
      if (input.checked) {
        applyTheme(input.value);
        if (document.getElementById('dashboard-charts-data') || document.getElementById('statistics-charts-data')) {
          window.location.reload();
        }
      }
    });
  });

  var menuLinks = document.querySelectorAll('[data-settings-link]');
  var sections = document.querySelectorAll('[data-settings-section]');

  function setActiveMenu(targetId) {
    menuLinks.forEach(function (link) {
      link.classList.toggle('active', link.getAttribute('data-settings-link') === targetId);
    });
  }

  menuLinks.forEach(function (link) {
    link.addEventListener('click', function () {
      setActiveMenu(link.getAttribute('data-settings-link'));
    });
  });

  if (sections.length && 'IntersectionObserver' in window) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          setActiveMenu(entry.target.getAttribute('data-settings-section'));
        }
      });
    }, { rootMargin: '-30% 0px -55% 0px', threshold: 0.1 });

    sections.forEach(function (section) {
      observer.observe(section);
    });
  }
})();
