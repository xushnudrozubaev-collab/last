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

  var attendancePage = document.querySelector('[data-attendance-page]');
  if (attendancePage) {
    var trainingSelect = document.getElementById('attendanceTrainingSelect');
    var refreshButton = document.getElementById('attendanceRefreshButton');
    var saveButton = document.getElementById('attendanceSaveButton');
    var rowsBody = document.getElementById('attendanceRows');
    var statsRowsBody = document.getElementById('attendanceStatsRows');
    var messageBox = document.querySelector('[data-attendance-message]');
    var durationBadge = document.querySelector('[data-attendance-duration]');
    var attendanceChartData = parseJsonScript('attendance-charts-data') || {};
    var attendanceCharts = {};
    var attendanceStatuses = ['Qatnashdi', 'Kelmadi', 'Kechikdi', 'Uzrli sabab'];
    var injuryStatuses = ["Yo'q", 'Bor', 'Tiklanmoqda'];

    function getCookie(name) {
      var value = '; ' + document.cookie;
      var parts = value.split('; ' + name + '=');
      if (parts.length === 2) return parts.pop().split(';').shift();
      return '';
    }

    function escapeHtml(value) {
      return String(value == null ? '' : value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }

    function showAttendanceMessage(text, tone) {
      if (!messageBox) return;
      messageBox.textContent = text || '';
      messageBox.className = 'attendance-message ' + (tone || '');
    }

    function optionList(options, selected) {
      return options.map(function (option) {
        return '<option value="' + escapeHtml(option) + '"' + (option === selected ? ' selected' : '') + '>' + escapeHtml(option) + '</option>';
      }).join('');
    }

    function loadTrainingAttendance() {
      var trainingId = trainingSelect ? trainingSelect.value : '';
      if (!trainingId) {
        if (rowsBody) rowsBody.innerHTML = '<tr><td colspan="9">Mashg\'ulot tanlanmagan</td></tr>';
        showAttendanceMessage("Mashg'ulot tanlanmagan", 'error');
        return;
      }
      showAttendanceMessage("Ma'lumotlar yuklanmoqda...", 'loading');
      if (rowsBody) rowsBody.innerHTML = '<tr><td colspan="9">Ma\'lumotlar yuklanmoqda...</td></tr>';
      fetch('/api/attendance/training/' + trainingId + '/', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(function (response) { return response.json(); })
        .then(function (payload) {
          if (!payload.success) throw new Error(payload.message || "Ma'lumotlar yuklanmadi");
          renderAttendanceRows(payload.data.records, payload.data.training.duration_minutes);
          if (durationBadge) {
            durationBadge.innerHTML = '<i class="bi bi-hourglass-split"></i>' + escapeHtml(payload.data.training.duration_display);
          }
          showAttendanceMessage('', '');
        })
        .catch(function (error) {
          if (rowsBody) rowsBody.innerHTML = '<tr><td colspan="9">Ma\'lumotlar yuklanmadi</td></tr>';
          showAttendanceMessage(error.message || "Ma'lumotlar yuklanmadi", 'error');
        });
    }

    function renderAttendanceRows(records, duration) {
      if (!rowsBody) return;
      if (!records || !records.length) {
        rowsBody.innerHTML = '<tr><td colspan="9">Hozircha ma\'lumot mavjud emas</td></tr>';
        return;
      }
      rowsBody.innerHTML = records.map(function (record, index) {
        var player = record.player || {};
        var minutes = record.attended_minutes == null ? duration : record.attended_minutes;
        return '<tr data-player-id="' + player.id + '" data-duration="' + duration + '">' +
          '<td>' + (index + 1) + '</td>' +
          '<td><strong>' + escapeHtml(player.full_name) + '</strong></td>' +
          '<td>' + escapeHtml(player.position) + '</td>' +
          '<td><select class="attendance-input" data-field="attendance_status">' + optionList(attendanceStatuses, record.attendance_status) + '</select></td>' +
          '<td><input class="attendance-input" data-field="attended_minutes" type="number" min="0" max="' + duration + '" value="' + minutes + '"></td>' +
          '<td><select class="attendance-input" data-field="fatigue_level">' + optionList(['1', '2', '3', '4', '5'], String(record.fatigue_level || 1)) + '</select></td>' +
          '<td><select class="attendance-input" data-field="activity_score">' + optionList(['1','2','3','4','5','6','7','8','9','10'], String(record.activity_score || 7)) + '</select></td>' +
          '<td><select class="attendance-input" data-field="injury_status">' + optionList(injuryStatuses, record.injury_status) + '</select></td>' +
          '<td><textarea class="attendance-input attendance-note" data-field="coach_note" rows="2" placeholder="Murabbiy izohi">' + escapeHtml(record.coach_note || '') + '</textarea></td>' +
        '</tr>';
      }).join('');

      rowsBody.querySelectorAll('[data-field="attendance_status"]').forEach(function (select) {
        select.addEventListener('change', function () {
          var row = select.closest('tr');
          var minutesInput = row ? row.querySelector('[data-field="attended_minutes"]') : null;
          if (!minutesInput) return;
          var durationValue = Number(row.getAttribute('data-duration') || minutesInput.max || 90);
          if (select.value === 'Kelmadi' || select.value === 'Uzrli sabab') {
            minutesInput.value = 0;
          } else if (Number(minutesInput.value || 0) === 0) {
            minutesInput.value = durationValue;
          }
        });
      });
    }

    function collectAttendanceRows() {
      var trainingId = trainingSelect ? trainingSelect.value : '';
      if (!trainingId) {
        showAttendanceMessage("Mashg'ulot tanlanmagan", 'error');
        return null;
      }
      var rows = Array.prototype.slice.call(rowsBody ? rowsBody.querySelectorAll('tr[data-player-id]') : []);
      var records = [];
      for (var i = 0; i < rows.length; i += 1) {
        var row = rows[i];
        var duration = Number(row.getAttribute('data-duration') || 90);
        var minutes = Number(row.querySelector('[data-field="attended_minutes"]').value);
        var fatigue = Number(row.querySelector('[data-field="fatigue_level"]').value);
        var activity = Number(row.querySelector('[data-field="activity_score"]').value);
        if (minutes < 0 || minutes > duration) {
          showAttendanceMessage("Qatnashgan daqiqa mashg'ulot davomiyligidan katta bo'lishi mumkin emas", 'error');
          return null;
        }
        if (fatigue < 1 || fatigue > 5) {
          showAttendanceMessage('Charchoq darajasi 1 dan 5 gacha bo\'lishi kerak', 'error');
          return null;
        }
        if (activity < 1 || activity > 10) {
          showAttendanceMessage('Faollik bahosi 1 dan 10 gacha bo\'lishi kerak', 'error');
          return null;
        }
        records.push({
          player_id: Number(row.getAttribute('data-player-id')),
          attendance_status: row.querySelector('[data-field="attendance_status"]').value,
          attended_minutes: minutes,
          training_duration_minutes: duration,
          fatigue_level: fatigue,
          activity_score: activity,
          injury_status: row.querySelector('[data-field="injury_status"]').value,
          coach_note: row.querySelector('[data-field="coach_note"]').value
        });
      }
      return { trainingId: trainingId, records: records };
    }

    function saveAttendanceRows() {
      var data = collectAttendanceRows();
      if (!data) return;
      showAttendanceMessage("Ma'lumotlar yuklanmoqda...", 'loading');
      fetch('/api/attendance/training/' + data.trainingId + '/save/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ records: data.records })
      })
        .then(function (response) { return response.json(); })
        .then(function (payload) {
          if (!payload.success) throw new Error(payload.message || "Ma'lumotlarni saqlashda xatolik yuz berdi");
          showAttendanceMessage("Ma'lumotlar muvaffaqiyatli saqlandi", 'success');
          refreshAttendanceStats();
        })
        .catch(function (error) {
          showAttendanceMessage(error.message || "Ma'lumotlarni saqlashda xatolik yuz berdi", 'error');
        });
    }

    function attendanceLevelLabel(value) {
      if (value > 80) return 'Yaxshi';
      if (value >= 60) return "O'rtacha";
      return "E'tibor talab qiladi";
    }

    function ratingLevelLabel(value) {
      if (value > 85) return 'Yuqori natija';
      if (value >= 70) return 'Barqaror';
      return 'Rivojlantirish kerak';
    }

    function renderStatsTable(players) {
      if (!statsRowsBody) return;
      if (!players || !players.length) {
        statsRowsBody.innerHTML = '<tr><td colspan="13">Hozircha ma\'lumot mavjud emas</td></tr>';
        return;
      }
      statsRowsBody.innerHTML = players.map(function (stat, index) {
        return '<tr>' +
          '<td>' + (index + 1) + '</td>' +
          '<td><strong>' + escapeHtml(stat.player_name) + '</strong></td>' +
          '<td>' + escapeHtml(stat.position) + '</td>' +
          '<td>' + stat.attended_trainings + '</td>' +
          '<td>' + stat.absent_trainings + '</td>' +
          '<td>' + stat.late_trainings + '</td>' +
          '<td>' + stat.excused_trainings + '</td>' +
          '<td><span class="attendance-progress-badge"><span class="mini-progress"><i style="width: ' + stat.attendance_percent + '%;"></i></span>' + stat.attendance_percent + '% · ' + attendanceLevelLabel(stat.attendance_percent) + '</span></td>' +
          '<td>' + stat.average_participation_percent + '%</td>' +
          '<td>' + stat.average_fatigue_level + '</td>' +
          '<td>' + stat.average_activity_score + '</td>' +
          '<td>' + stat.injury_count + ' bor / ' + stat.recovering_count + ' tiklanmoqda</td>' +
          '<td><span class="rating-badge">' + stat.overall_activity_rating + '% · ' + ratingLevelLabel(stat.overall_activity_rating) + '</span></td>' +
        '</tr>';
      }).join('');
    }

    function updateAttendanceCards(teamStats) {
      if (!teamStats) return;
      var cardMap = {
        total_trainings: teamStats.total_trainings,
        average_attendance_percent: teamStats.average_attendance_percent + '%',
        average_activity_score: teamStats.average_activity_score + '/10',
        top_player: teamStats.top_player ? teamStats.top_player.player_name : '-',
        most_absent_player: teamStats.most_absent_player ? teamStats.most_absent_player.player_name : '-',
        injury_related_count: teamStats.injury_related_count
      };
      Object.keys(cardMap).forEach(function (key) {
        var element = document.querySelector('[data-stat="' + key + '"]');
        if (element) element.textContent = cardMap[key];
      });
    }

    function renderAttendanceCharts(chartData) {
      if (!chartData || typeof Chart === 'undefined') return;
      var theme = getChartTheme();
      Object.keys(attendanceCharts).forEach(function (key) {
        if (attendanceCharts[key]) attendanceCharts[key].destroy();
      });
      attendanceCharts = {};

      var percentCanvas = document.getElementById('attendancePercentChart');
      if (percentCanvas && chartData.labels && chartData.labels.length) {
        attendanceCharts.percent = new Chart(percentCanvas, {
          type: 'bar',
          data: {
            labels: chartData.labels,
            datasets: [{ label: 'Davomad foizi', data: chartData.attendance, backgroundColor: '#3B82F6', borderRadius: 10 }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              y: { beginAtZero: true, suggestedMax: 100, ticks: { color: theme.axis, callback: function (value) { return value + '%'; } }, grid: { color: theme.grid } },
              x: { ticks: { color: theme.axis }, grid: { display: false } }
            }
          }
        });
      }

      var ratingCanvas = document.getElementById('attendanceRatingChart');
      if (ratingCanvas && chartData.labels && chartData.labels.length) {
        attendanceCharts.rating = new Chart(ratingCanvas, {
          type: 'bar',
          data: {
            labels: chartData.labels,
            datasets: [{ label: 'Umumiy reyting', data: chartData.ratings, backgroundColor: '#22C55E', borderRadius: 10 }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              y: { beginAtZero: true, suggestedMax: 100, ticks: { color: theme.axis, callback: function (value) { return value + '%'; } }, grid: { color: theme.grid } },
              x: { ticks: { color: theme.axis }, grid: { display: false } }
            }
          }
        });
      }

      var statusCanvas = document.getElementById('attendanceStatusChart');
      if (statusCanvas && chartData.statusLabels && chartData.statusLabels.length) {
        attendanceCharts.status = new Chart(statusCanvas, {
          type: 'bar',
          data: {
            labels: chartData.statusLabels,
            datasets: [{ label: 'Holatlar soni', data: chartData.statusValues, backgroundColor: ['#22C55E', '#EF4444', '#F59E0B', '#3B82F6'], borderRadius: 10 }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              y: { beginAtZero: true, ticks: { color: theme.axis, precision: 0 }, grid: { color: theme.grid } },
              x: { ticks: { color: theme.axis }, grid: { display: false } }
            }
          }
        });
      }
    }

    function refreshAttendanceStats() {
      Promise.all([
        fetch('/api/attendance/stats/team/').then(function (response) { return response.json(); }),
        fetch('/api/attendance/stats/players/').then(function (response) { return response.json(); })
      ]).then(function (responses) {
        var teamPayload = responses[0];
        var playersPayload = responses[1];
        if (teamPayload.success) updateAttendanceCards(teamPayload.data);
        if (playersPayload.success) {
          var players = playersPayload.data.players || [];
          renderStatsTable(players);
          renderAttendanceCharts({
            labels: players.filter(function (item) { return item.total_marked_trainings; }).map(function (item) { return item.player_name; }),
            attendance: players.filter(function (item) { return item.total_marked_trainings; }).map(function (item) { return item.attendance_percent; }),
            ratings: players.filter(function (item) { return item.total_marked_trainings; }).map(function (item) { return item.overall_activity_rating; }),
            statusLabels: teamPayload.data ? Object.keys(teamPayload.data.status_counts || {}) : [],
            statusValues: teamPayload.data ? Object.keys(teamPayload.data.status_counts || {}).map(function (key) { return teamPayload.data.status_counts[key]; }) : []
          });
        }
      });
    }

    if (refreshButton) refreshButton.addEventListener('click', loadTrainingAttendance);
    if (saveButton) saveButton.addEventListener('click', saveAttendanceRows);
    if (trainingSelect) trainingSelect.addEventListener('change', loadTrainingAttendance);
    renderAttendanceCharts(attendanceChartData);
    loadTrainingAttendance();
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
        if (document.getElementById('dashboard-charts-data') || document.getElementById('statistics-charts-data') || document.getElementById('attendance-charts-data')) {
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
