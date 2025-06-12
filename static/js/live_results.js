  const ctx = document.getElementById('votesChart').getContext('2d');
  let chart;

  async function fetchVotesData() {
    const response = await fetch('/api/votes_data');
    return await response.json();
  }

  function updateVotesTable(data) {
    const tableBody = document.getElementById('votesTableBody');
    tableBody.innerHTML = ''; // Clear old rows

    data.names.forEach((name, index) => {
      const logo = data.logos[index]; // Logo filename
      const votes = data.votes[index];

      const row = document.createElement('tr');
      row.innerHTML = `
        <td style="padding: 10px; border: 1px solid #dee2e6; display: flex; align-items: center; gap: 10px;">
          <img src="/static/party_logos/${logo}" alt="${name} logo" width="30" height="30" style="border-radius: 50%; object-fit: cover;">
          <span>${name}</span>
        </td>
        <td style="padding: 10px; border: 1px solid #dee2e6;">${votes}</td>
      `;
      tableBody.appendChild(row);
    });
  }

  async function createOrUpdateChart() {
    const data = await fetchVotesData();

    if (chart) {
      // Update existing chart
      chart.data.labels = data.names;
      chart.data.datasets[0].data = data.votes;
      chart.data.datasets[0].backgroundColor = data.colors;
      chart.data.datasets[0].borderColor = data.colors;
      chart.update();
    } else {
      // Create new chart
      chart = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: data.names,
          datasets: [{
            // Removed 'label' to avoid clickable legend
            data: data.votes,
            backgroundColor: data.colors,
            borderColor: data.colors,
            borderWidth: 1,
            borderRadius: 4,
            maxBarThickness: 40
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: { duration: 500 },
          scales: {
            y: {
              beginAtZero: true,
              precision: 0,
              ticks: { stepSize: 1, color: '#495057' },
              grid: { color: '#e9ecef' }
            },
            x: {
              ticks: { color: '#495057' },
              grid: { display: false }
            }
          },
          plugins: {
            legend: {
              display: false // ✅ Completely remove legend
            },
            tooltip: {
              enabled: true,
              backgroundColor: '#ffffff',
              titleColor: '#212529',
              bodyColor: '#212529',
              borderColor: '#ced4da',
              borderWidth: 1,
              boxPadding: 6
            }
          }
        }
      });
    }

    updateVotesTable(data);
  }

  // Initial load and auto-update every 5 seconds
  createOrUpdateChart();
  setInterval(createOrUpdateChart, 5000);
