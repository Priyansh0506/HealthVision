// predict.js
// handles symptom search, selection, and calling the prediction API

let selectedSymptoms = [];

// filter the symptom list based on what user types in the search box
function filterSymptoms(query) {
    const items = document.querySelectorAll('.symptom-item');
    const q = query.toLowerCase();
    items.forEach(item => {
        const matches = item.textContent.toLowerCase().includes(q);
        item.style.display = matches ? 'flex' : 'none';
    });
}

// called when a checkbox is checked/unchecked
function toggleSymptom(checkbox) {
    const val = checkbox.value;

    if (checkbox.checked) {
        if (!selectedSymptoms.includes(val)) {
            selectedSymptoms.push(val);
            checkbox.closest('.symptom-item').classList.add('selected');
        }
    } else {
        selectedSymptoms = selectedSymptoms.filter(s => s !== val);
        checkbox.closest('.symptom-item').classList.remove('selected');
    }

    updateTagsArea();
}

// re-render the tags area whenever selected symptoms change
function updateTagsArea() {
    const tagsBox = document.getElementById('tags-area');
    const countEl = document.getElementById('count-text');

    countEl.textContent = selectedSymptoms.length + ' symptoms selected';

    if (selectedSymptoms.length === 0) {
        tagsBox.innerHTML = '<span class="empty-msg">No symptoms selected yet...</span>';
        return;
    }

    tagsBox.innerHTML = '';
    selectedSymptoms.forEach(sym => {
        const tag = document.createElement('div');
        tag.className = 'sym-tag';
        tag.innerHTML = `
            ${sym.replace(/_/g, ' ')}
            <span class="remove" onclick="removeSymptom('${sym}')">×</span>
        `;
        tagsBox.appendChild(tag);
    });
}

// remove a symptom from selection (also unchecks the checkbox)
function removeSymptom(sym) {
    selectedSymptoms = selectedSymptoms.filter(s => s !== sym);

    document.querySelectorAll('.symptom-item input').forEach(cb => {
        if (cb.value === sym) {
            cb.checked = false;
            cb.closest('.symptom-item').classList.remove('selected');
        }
    });

    updateTagsArea();
}

// main function - sends symptoms to backend and shows results
async function runPrediction() {
    if (selectedSymptoms.length === 0) {
        alert('Please select at least one symptom first.');
        return;
    }

    document.getElementById('loading-box').style.display = 'block';
    document.getElementById('results-section').style.display = 'none';
    document.getElementById('predict-btn').disabled = true;

    try {
        const response = await fetch('/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symptoms: selectedSymptoms })
        });

        const data = await response.json();

        if (data.error) {
            alert(data.error);
            return;
        }

        displayResults(data);

        // save this prediction to history
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
        console.log('prediction error:', err);
        alert('Something went wrong. Please try again.');
    } finally {
        document.getElementById('loading-box').style.display = 'none';
        document.getElementById('predict-btn').disabled = false;
    }
}

// fill in all the result fields with the response data
function displayResults(data) {
    document.getElementById('results-section').style.display = 'block';

    // show emergency alert if needed
    const emergAlert = document.getElementById('emergency-alert');
    emergAlert.style.display = data.emergency ? 'block' : 'none';

    // main prediction
    document.getElementById('disease-name').textContent = data.disease;
    document.getElementById('conf-text').textContent = data.confidence + '%';
    document.getElementById('conf-fill').style.width = data.confidence + '%';
    document.getElementById('doctor-name').textContent = data.doctor;

    // top 3 possible diseases
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

    // disease description
    document.getElementById('desc-text').textContent = data.description;

    // precautions list
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
        precDiv.innerHTML = '<p style="font-size:13px; color:#b2bec3;">No precautions available.</p>';
    }

    // scroll down to results
    document.getElementById('results-section').scrollIntoView({ behavior: 'smooth' });
}
