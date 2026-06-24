import pandas as pd
import numpy as np
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.tree import DecisionTreeClassifier
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import warnings

warnings.filterwarnings('ignore')

app = Flask(__name__)
app.secret_key = "healthvision_secret_123"

# load all the csv files we need
df = pd.read_csv('dataset.csv')
severity_df = pd.read_csv('Symptom-severity.csv')
desc_df = pd.read_csv('symptom_Description.csv')
prec_df = pd.read_csv('symptom_precaution.csv')

# get list of all symptoms from severity file, sorted alphabetically
all_symptoms = sorted(severity_df['Symptom'].str.strip().str.replace(' ', '_').tolist())

# clean up the dataset - fill blanks and fix spacing in symptom columns
df = df.fillna(0)
for col in df.columns[1:]:
    if df[col].dtype == 'object':
        df[col] = df[col].str.strip().str.replace(' ', '_')

# convert symptoms into a binary feature vector (1 if symptom present, else 0)
def make_feature_vector(symptom_list):
    return [1 if s in symptom_list else 0 for s in all_symptoms]

# build X (features) and y (labels) from dataset
X = []
y = []
for _, row in df.iterrows():
    present = [row[c] for c in df.columns[1:] if row[c] != 0]
    X.append(make_feature_vector(present))
    y.append(row['Disease'])

X = np.array(X)
y = np.array(y)

# train/test split and train the random forest model
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)

rf_accuracy = accuracy_score(y_test, rf_model.predict(X_test))
print(f"RF Accuracy: {rf_accuracy:.2%}")

# also train a decision tree for comparison on the stats page
dt_model = DecisionTreeClassifier(random_state=42)
dt_model.fit(X_train, y_train)
dt_accuracy = accuracy_score(y_test, dt_model.predict(X_test))
print(f"DT Accuracy: {dt_accuracy:.2%}")

# symptoms that might indicate a medical emergency
EMERGENCY_SYMPTOMS = {
    'chest_pain', 'shortness_of_breath', 'severe_headache',
    'neck_stiffness', 'loss_of_consciousness', 'sweating'
}

# map diseases to the right type of doctor
DISEASE_TO_DOCTOR = {
    'Heart Attack': 'Cardiologist',
    'Diabetes': 'Endocrinologist',
    'Pneumonia': 'Pulmonologist',
    'Tuberculosis': 'Pulmonologist',
    'Hepatitis A': 'Gastroenterologist',
    'Hepatitis B': 'Gastroenterologist',
    'Malaria': 'General Physician',
    'Dengue': 'General Physician',
    'Fungal infection': 'Dermatologist',
    'Allergy': 'Allergist',
    'Migraine': 'Neurologist',
    'Hypertension': 'Cardiologist',
    'Arthritis': 'Rheumatologist',
    'Asthma': 'Pulmonologist',
}

def get_recommended_doctor(disease):
    return DISEASE_TO_DOCTOR.get(disease, 'General Physician')

def run_prediction(user_symptoms):
    cleaned = [s.strip().replace(' ', '_') for s in user_symptoms]
    vec = np.array(make_feature_vector(cleaned)).reshape(1, -1)

    predicted = rf_model.predict(vec)[0]
    probabilities = rf_model.predict_proba(vec)[0]
    confidence = round(float(max(probabilities)) * 100, 1)

    # get top 3 possible diseases
    top3_indices = np.argsort(probabilities)[-3:][::-1]
    top3 = [(rf_model.classes_[i], round(float(probabilities[i]) * 100, 1)) for i in top3_indices]

    is_emergency = bool(set(cleaned) & EMERGENCY_SYMPTOMS)

    return {
        'disease': predicted,
        'confidence': confidence,
        'top3': top3,
        'doctor': get_recommended_doctor(predicted),
        'emergency': is_emergency
    }


# ---- routes ----

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', symptoms=all_symptoms)


@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    symptoms = data.get('symptoms', [])

    if not symptoms:
        return jsonify({'error': 'No symptoms provided'})

    result = run_prediction(symptoms)

    # get description and precautions for the predicted disease
    desc_row = desc_df[desc_df['Disease'] == result['disease']]
    prec_row = prec_df[prec_df['Disease'] == result['disease']]

    if len(desc_row) > 0:
        result['description'] = desc_row['Description'].values[0]
    else:
        result['description'] = 'No description available.'

    precautions = []
    if len(prec_row) > 0:
        for i in range(1, 5):
            col = f'Precaution_{i}'
            if col in prec_row.columns:
                val = prec_row[col].values[0]
                if val and str(val) != 'nan':
                    precautions.append(val)
    result['precautions'] = precautions

    return jsonify(result)


@app.route('/model-stats')
def model_stats():
    # feature importance from the RF model
    importances = rf_model.feature_importances_
    top_indices = np.argsort(importances)[-10:][::-1]

    top_symptoms = []
    for i in top_indices:
        top_symptoms.append({
            'symptom': all_symptoms[i].replace('_', ' ').title(),
            'importance': round(float(importances[i]) * 100, 2)
        })

    return jsonify({
        'rf_accuracy': round(rf_accuracy * 100, 2),
        'dt_accuracy': round(dt_accuracy * 100, 2),
        'top_symptoms': top_symptoms,
        'total_diseases': len(set(y)),
        'total_symptoms': len(all_symptoms),
        'training_samples': len(X_train)
    })


@app.route('/history', methods=['GET', 'POST'])
def history():
    if request.method == 'POST':
        data = request.get_json()

        if not hasattr(app, 'prediction_history'):
            app.prediction_history = []

        app.prediction_history.append({
            'symptoms': data.get('symptoms', []),
            'disease': data.get('disease', ''),
            'confidence': data.get('confidence', 0),
            'doctor': data.get('doctor', '')
        })

        # only keep last 5
        if len(app.prediction_history) > 5:
            app.prediction_history = app.prediction_history[-5:]

        return jsonify({'status': 'saved'})

    if not hasattr(app, 'prediction_history'):
        app.prediction_history = []

    return jsonify(app.prediction_history)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        conn = sqlite3.connect('disease.db')
        cur = conn.cursor()

        try:
            cur.execute(
                "INSERT INTO users(username, email, password) VALUES(?, ?, ?)",
                (username, email, password)
            )
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except Exception as e:
            conn.close()
            return f"Error: {str(e)}"

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('disease.db')
        cur = conn.cursor()
        cur.execute("SELECT id, username, password FROM users WHERE email=?", (email,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('home'))
        else:
            return "Invalid email or password ❌"

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
