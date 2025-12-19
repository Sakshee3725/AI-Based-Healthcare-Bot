import pandas as pd
from sklearn.tree import DecisionTreeClassifier
import pickle
import os

data = pd.read_csv("dataset/symptoms_disease.csv")

X = data.drop("disease", axis=1)
y = data["disease"]

model = DecisionTreeClassifier()
model.fit(X, y)

os.makedirs("model", exist_ok=True)

with open("model/disease_model.pkl", "wb") as f:
    pickle.dump(model, f)

print("Model trained and saved successfully!")
