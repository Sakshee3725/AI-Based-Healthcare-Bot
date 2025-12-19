import pickle
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from sklearn.model_selection import train_test_split

# ---------------- LOAD DATASET ----------------
# Example dataset (replace with your real dataset if you have one)
# Symptoms: fever, cough, headache, fatigue, nausea
X = np.array([
    [1,1,0,1,0],
    [1,0,1,1,0],
    [0,1,0,0,0],
    [0,0,1,1,1],
    [1,1,1,1,0],
    [0,0,0,1,1],
    [1,0,0,0,0],
    [0,1,1,0,0]
])

y = np.array([
    "Flu",
    "Flu",
    "Cold",
    "Migraine",
    "Flu",
    "Migraine",
    "Cold",
    "Cold"
])

# ---------------- SPLIT DATA ----------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42
)

# ---------------- LOAD TRAINED MODEL ----------------
model = pickle.load(open("model/disease_model.pkl", "rb"))

# ---------------- PREDICTION ----------------
y_pred = model.predict(X_test)

# ---------------- ACCURACY ----------------
accuracy = accuracy_score(y_test, y_pred)
print("Model Accuracy:", round(accuracy * 100, 2), "%")

# ---------------- CONFUSION MATRIX ----------------
cm = confusion_matrix(y_test, y_pred)
print("\nConfusion Matrix:\n", cm)

# ---------------- CLASSIFICATION REPORT ----------------
print("\nClassification Report:\n")
print(classification_report(y_test, y_pred))

# ---------------- PLOT CONFUSION MATRIX ----------------
plt.figure(figsize=(5,5))
plt.imshow(cm)
plt.title("Confusion Matrix")
plt.colorbar()
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.show()
