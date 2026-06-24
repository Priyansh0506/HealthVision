// predict.js - handles symptom selection and prediction

let selectedSymptoms = [];

// filter symptom list on search
function filterSymptoms(query) {
    const items = document.querySelectorAll('.symptom-item');
    items.forEach(item => {
        const text = item.textContent.toLowerCase();
        item.style.display = text.includes(query.toLowerCase()) ? 'flex' : 'none';
    });
}

// add or remove symptom from selected list
function toggleSymptom(checkbox) {
    const val = checkbox.value;
    const label = checkbox.closest('.symptom-item');

    if (checkbox.checked) {
        if (!selectedSymptoms.includes(val)) {
            selectedSymptoms.push(val);
            label.classList.add('selected');
        }
    } else {
        selectedSymptoms = selectedSymptoms.filter(s => s !== val);
        label.classList.remove('selected');
    }

    refreshTagsArea();
}

// update the tags display area
function refreshTagsArea() {
    const box = document.getElementById('tags-area');
    const countEl = document.getElementById('count-text');

    countEl.textContent = selectedSymptoms.length + ' symptoms selected';

    if (selectedSymptoms.length === 0) {
        box.innerHTML = '<span class="empty-msg">No symptoms selected yet...</span>';
        return;
    }

    box.innerHTML = '';
    selectedSymptoms.forEach(sym => {
        const tag = document.createElement('div');
        tag.className = 'sym-tag';
        tag.innerHTML = `
            ${sym.replace(/_/g, ' ')}
            <span class="remove" onclick="removeSymptom('${sym}')">×</span>
        `;
        box.appendChild(tag);
    });
}

// remove a symptom from tags
function removeSymptom(sym) {
    selectedSymptoms = selectedSymptoms.filter(s => s !== sym);

    // uncheck the checkbox too
    document.querySelectorAll('.symptom-item input').forEach(cb => {
        if (cb.value === sym) {
            cb.checked = false;
            cb.closest('.symptom-item').classList.remove('selected');
        }
    });

    refreshTagsArea();
}

// main predict function
async function runPrediction() {
    if (selectedSymptoms.length === 0) {
        alert('Please select at least one symptom.');
        return;
    }

    // show loading, hide results
    document.getElementById('loading-box').style.display = 'block';
    document.getElementById('results-section').style.display = 'none';
    document.getElementById('predict-btn').disabled = true;

    try {
        const res = await fetch('/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symptoms: selectedSymptoms })
        });

        const data = await res.json();

        if (data.error) {
            alert(data.error);
            return;
        }

        showResults(data);

        // save to history
        await fetch('/history', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                symptoms: selectedSymptoms,
                disease: data.disease,
                confidence: data.confidence,
                doctor: data.doctor
            })
        });

        loadHistory();

    } catch (err) {
        alert('Something went wrong. Please try again.');
        console.log('predict error:', err);
    } finally {
        document.getElementById('loading-box').style.display = 'none';
        document.getElementById('predict-btn').disabled = false;
    }
}

// fill in the results section
function showResults(data) {
    document.getElementById('results-section').style.display = 'block';

    // emergency alert
    const emergBox = document.getElementById('emergency-alert');
    emergBox.style.display = data.emergency ? 'block' : 'none';

    // disease and confidence
    document.getElementById('disease-name').textContent = data.disease;
    document.getElementById('conf-text').textContent = data.confidence + '%';
    document.getElementById('conf-fill').style.width = data.confidence + '%';
    document.getElementById('doctor-name').textContent = data.doctor;

    // top 3 predictions
    const top3Div = document.getElementById('top3-list');
    top3Div.innerHTML = '';
    data.top3.forEach(([name, prob]) => {
        top3Div.innerHTML += `
            <div class="top3-item">
                <div class="top3-row">
                    <span>${name}</span>
                    <span style="font-weight:600; color:#1e3a5f;">${prob}%</span>
                </div>
                <div class="hv-bar">
                    <div class="hv-bar-fill" style="width:${prob}%"></div>
                </div>
            </div>
        `;
    });

    // description
    document.getElementById('desc-text').textContent = data.description;

    // precautions
    const precDiv = document.getElementById('prec-list');
    precDiv.innerHTML = '';
    if (data.precautions && data.precautions.length > 0) {
        data.precautions.forEach(p => {
            precDiv.innerHTML += `
                <div class="prec-item">
                    <span class="prec-check">✓</span>
                    <span>${p}</span>
                </div>
            `;
        });
    } else {
        precDiv.innerHTML = '<p class="text-muted" style="font-size:13px;">No precautions found.</p>';
    }

    // scroll to results
    document.getElementById('results-section').scrollIntoView({ behavior: 'smooth' });
}