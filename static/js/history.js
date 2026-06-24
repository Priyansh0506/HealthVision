// history.js - load and display recent predictions

async function loadHistory() {
    try {
        const res = await fetch('/history');
        const data = await res.json();

        const histDiv = document.getElementById('history-list');

        if (data.length === 0) {
            histDiv.innerHTML = '<p class="text-muted" style="font-size:14px;">No predictions made yet.</p>';
            return;
        }

        histDiv.innerHTML = '';
        data.forEach((item, i) => {
            histDiv.innerHTML += `
                <div class="history-item">
                    <div class="history-num">${i + 1}</div>
                    <div>
                        <div style="font-weight:600; margin-bottom:2px;">${item.disease}</div>
                        <div style="font-size:12px; color:#636e72;">
                            ${item.confidence}% confidence &nbsp;·&nbsp; ${item.doctor}
                        </div>
                    </div>
                </div>
            `;
        });

    } catch (err) {
        console.log('history load error:', err);
    }
}