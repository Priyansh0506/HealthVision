// stats.js
// loads model comparison stats and top symptoms from the backend

async function loadModelStats() {
    try {
        const res = await fetch('/model-stats');
        const data = await res.json();

        // update accuracy bars
        document.getElementById('rf-acc').textContent = data.rf_accuracy + '%';
        document.getElementById('dt-acc').textContent = data.dt_accuracy + '%';
        document.getElementById('rf-bar').style.width = data.rf_accuracy + '%';
        document.getElementById('dt-bar').style.width = data.dt_accuracy + '%';

        // update summary numbers
        document.getElementById('stat-diseases').textContent = data.total_diseases;
        document.getElementById('stat-symptoms').textContent = data.total_symptoms;
        document.getElementById('stat-samples').textContent = data.training_samples;

        // top symptoms by feature importance
        const container = document.getElementById('top-symptoms');
        container.innerHTML = '';
        data.top_symptoms.forEach(item => {
            // multiply importance by 8 so bars are visible (values are small)
            const barWidth = Math.min(item.importance * 8, 100);
            container.innerHTML += `
                <div class="top3-item">
                    <div class="top3-row">
                        <span>${item.symptom}</span>
                        <span style="color:#636e72;">${item.importance}%</span>
                    </div>
                    <div class="hv-bar">
                        <div class="hv-bar-fill" style="width:${barWidth}%"></div>
                    </div>
                </div>
            `;
        });

    } catch (err) {
        console.log('could not load model stats:', err);
    }
}
