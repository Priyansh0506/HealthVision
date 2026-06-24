// history.js
// fetches and displays the last 5 predictions

async function loadHistory() {
    try {
        const res = await fetch('/history');
        const data = await res.json();

        const histDiv = document.getElementById('history-list');

        if (data.length === 0) {
            histDiv.innerHTML = '<p class="text-muted" style="font-size:14px;">No predictions yet.</p>';
            return;
        }

        histDiv.innerHTML = '';
        data.forEach((entry, index) => {
            histDiv.innerHTML += `
                <div class="history-item">
                    <div class="history-num">${index + 1}</div>
                    <div>
                        <div style="font-weight:600; margin-bottom:2px;">${entry.disease}</div>
                        <div style="font-size:12px; color:#636e72;">
                            ${entry.confidence}% confidence &nbsp;·&nbsp; ${entry.doctor}
                        </div>
                    </div>
                </div>
            `;
        });

    } catch (err) {
        console.log('history fetch failed:', err);
    }
}
