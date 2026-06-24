// stats.js - loads model comparison and top symptoms

async function loadModelStats() {
    try {
        const res = await fetch('/model-stats');
        const data = await res.json();

        document.getElementById('rf-acc').textContent = data.rf_accuracy + '%';
        document.getElementById('dt-acc').textContent = data.dt_accuracy + '%';
        document.getElementById('rf-bar').style.width = data.rf_accuracy + '%';
        document.getElementById('dt-bar').style.width = data.dt_accuracy + '%';

        document.getElementById('stat-diseases').textContent = data.total_diseases;
        document.getElementById('stat-symptoms').textContent = data.total_symptoms;
        document.getElementById('stat-samples').textContent = data.training_samples;

        // top symptoms list
        const symDiv = document.getElementById('top-symptoms');
        symDiv.innerHTML = '';
        data.top_symptoms.forEach(item => {
            symDiv.innerHTML += `
                <div class="top3-item">
                    <div class="top3-row">
                        <span>${item.symptom}</span>
                        <span style="color:#636e72;">${item.importance}%</span>
                    </div>
                    <div class="hv-bar">
                        <div class="hv-bar-fill" style="width:${Math.min(item.importance * 8, 100)}%"></div>
                    </div>
                </div>
            `;
        });

    } catch (err) {
        console.log('stats load error:', err);
    }
}