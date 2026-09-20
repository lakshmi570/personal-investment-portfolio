fetch('/api/chart-data')
  .then(res => res.json())
  .then(data => {
    if (!data.labels || data.labels.length === 0) return;

    const colors = ['#4299e1','#68d391','#f6ad55','#fc8181','#b794f4','#76e4f7','#fbb6ce'];

    // Donut Chart
    new Chart(document.getElementById('donutChart'), {
      type: 'doughnut',
      data: {
        labels: data.labels,
        datasets: [{ data: data.values, backgroundColor: colors, borderWidth: 2 }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'bottom' },
          tooltip: {
            callbacks: {
              label: ctx => ' ₹' + ctx.parsed.toLocaleString('en-IN', { minimumFractionDigits: 2 })
            }
          }
        }
      }
    });

    // Bar Chart
    new Chart(document.getElementById('barChart'), {
      type: 'bar',
      data: {
        labels: data.labels,
        datasets: [{
          label: 'Current Value (₹)',
          data: data.values,
          backgroundColor: colors,
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          y: {
            ticks: {
              callback: val => '₹' + val.toLocaleString('en-IN')
            }
          }
        }
      }
    });
  });
