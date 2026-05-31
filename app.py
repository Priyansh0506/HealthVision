import pandas as pd
import numpy as np
from flask import Flask, render_template, request, jsonify
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import warnings
from flask import session, redirect, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
warnings.filterwarnings('ignore')

app = Flask(__name__)
app.secret_key = "medipredict_secret_key"
def get_db_connection():
    conn = sqlite3.connect('disease.db')
    conn.row_factory = sqlite3.Row
    return conn

df = pd.read_csv('dataset.csv')
severity_df = pd.read_csv('Symptom-severity.csv')
description_df = pd.read_csv('symptom_Description.csv')
precaution_df = pd.read_csv('symptom_precaution.csv')

all_symptoms = sorted(list(severity_df['Symptom'].str.strip().str.replace(' ', '_')))

df = df.fillna(0)
for col in df.columns[1:]:
    if df[col].dtype == 'object':
        df[col] = df[col].str.strip().str.replace(' ', '_')

def get_features(symptom_list):
    return [1 if s in symptom_list else 0 for s in all_symptoms]

X, y = [], []
for _, row in df.iterrows():
    symptoms = [row[col] for col in df.columns[1:] if row[col] != 0]
    X.append(get_features(symptoms))
    y.append(row['Disease'])

X = np.array(X)
y = np.array(y)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)
accuracy = accuracy_score(y_test, model.predict(X_test))
print(f"Model Accuracy: {accuracy:.2%}")

EMERGENCY_SYMPTOMS = {
    'chest_pain', 'shortness_of_breath', 'severe_headache',
    'neck_stiffness', 'loss_of_consciousness', 'sweating'
}

DOCTOR_REFERRAL = {
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

def get_doctor(disease):
    return DOCTOR_REFERRAL.get(disease, 'General Physician')

def predict_disease(user_symptoms):
    cleaned = [s.strip().replace(' ', '_') for s in user_symptoms]
    features = np.array(get_features(cleaned)).reshape(1, -1)

    disease = model.predict(features)[0]
    probs = model.predict_proba(features)[0]
    confidence = round(float(max(probs)) * 100, 1)

    top3_idx = np.argsort(probs)[-3:][::-1]
    top3 = [(model.classes_[i], round(float(probs[i]) * 100, 1)) for i in top3_idx]

    is_emergency = bool(set(cleaned) & EMERGENCY_SYMPTOMS)

    return {
        'disease': disease,
        'confidence': confidence,
        'top3': top3,
        'doctor': get_doctor(disease),
        'emergency': is_emergency
    }

@app.route('/')
def home():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template(
        'index.html',
        symptoms=all_symptoms
    )

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    user_symptoms = data.get('symptoms', [])

    if not user_symptoms:
        return jsonify({'error': 'No symptoms provided'})

    result = predict_disease(user_symptoms)

    desc_row = description_df[description_df['Disease'] == result['disease']]
    prec_row = precaution_df[precaution_df['Disease'] == result['disease']]

    description = desc_row['Description'].values[0] if len(desc_row) > 0 else 'No description available'

    precautions = []
    if len(prec_row) > 0:
        for i in range(1, 5):
            col = f'Precaution_{i}'
            if col in prec_row.columns:
                val = prec_row[col].values[0]
                if val and str(val) != 'nan':
                    precautions.append(val)

    result['description'] = description
    result['precautions'] = precautions

    return jsonify(result)
@app.route('/model-stats')
def model_stats():
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.svm import SVC
    
    dt = DecisionTreeClassifier(random_state=42)
    dt.fit(X_train, y_train)
    dt_acc = round(accuracy_score(y_test, dt.predict(X_test)) * 100, 2)
    
    rf_acc = round(accuracy * 100, 2)
    
    top_symptoms = []
    importances = model.feature_importances_
    top_idx = np.argsort(importances)[-10:][::-1]
    for i in top_idx:
        top_symptoms.append({
            'symptom': all_symptoms[i].replace('_', ' ').title(),
            'importance': round(float(importances[i]) * 100, 2)
        })
    
    return jsonify({
        'rf_accuracy': rf_acc,
        'dt_accuracy': dt_acc,
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

        conn = sqlite3.connect("disease.db")
        cur = conn.cursor()

        try:
            cur.execute(
                "INSERT INTO users(username,email,password) VALUES(?,?,?)",
                (username, email, password)
            )
            conn.commit()
            conn.close()

            return redirect(url_for('login'))

        except Exception as e:
            conn.close()
            return f"Error: {str(e)}"

    return render_template("register.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect("disease.db")
        cur = conn.cursor()

        cur.execute(
            "SELECT id, username, password FROM users WHERE email=?",
            (email,)
        )

        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('home'))
        else:
            return "Invalid Email or Password ❌"
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
    
if __name__ == '__main__':
    app.run(debug=True)