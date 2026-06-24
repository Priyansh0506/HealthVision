HealthVision

HealthVision is a machine learning-based web application that predicts diseases from user symptoms and provides basic information like precautions, descriptions, and recommended specialists.

I built this project to get hands-on experience with the complete ML workflow and to move beyond notebooks by creating a full-stack application with authentication, a database, and a user-friendly interface.

Features

- Search and select from 132 symptoms.
- Predict the most likely disease with a confidence score.
- Show the top 3 possible diseases.
- Recommend the appropriate doctor/specialist.
- Display disease descriptions and precautions.
- User registration and login system.
- Store prediction history for each user.
- Compare Random Forest and Decision Tree performance.

Tech Stack

- Backend: Flask, Python
- Machine Learning: scikit-learn (Random Forest Classifier)
- Database: SQLite
- Frontend: HTML, CSS, JavaScript
- Authentication: Flask Sessions

Dataset

The model was trained on a symptom-disease dataset containing 41+ diseases and 132 symptoms. Additional files provide disease descriptions, symptom severity weights, and precaution recommendations.

Model Performance

I experimented with multiple models and found that Random Forest achieved around 93% accuracy, outperforming a Decision Tree baseline. Therefore, Random Forest is used for the final predictions.

Live Demo

🌐 Try it here: https://healthvision-wbp2.onrender.com

Running Locally

git clone https://github.com/Priyansh0506/HealthVision.git
cd HealthVision
pip install -r requirements.txt
python app.py

Then open:

http://127.0.0.1:5000

Project Structure

HealthVision/
├── app.py
├── database.py
├── check_users.py
├── dataset.csv
├── disease.db
├── static/
│   ├── css/
│   └── js/
└── templates/
    ├── base.html
    ├── index.html
    ├── login.html
    └── register.html

Disclaimer

This project is intended for educational purposes only. Predictions should not be considered medical advice. Always consult a qualified healthcare professional for diagnosis and treatment.

Future Improvements

- Better model evaluation metrics and confusion matrix.
- Improved mobile responsiveness.
- PostgreSQL support for scalability.
- Docker and cloud deployment.
- More diseases and symptom coverage.
