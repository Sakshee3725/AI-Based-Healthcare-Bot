import pickle

with open("model/disease_model.pkl", "rb") as f:
    model = pickle.load(f)

symptoms = ["fever", "cough", "headache", "fatigue", "nausea"]

print("🤖 AI Healthcare Bot")
print("Answer with yes or no\n")

user_input = []

for symptom in symptoms:
    answer = input(f"Do you have {symptom}? ").lower()
    user_input.append(1 if answer == "yes" else 0)

prediction = model.predict([user_input])[0]

print("\n🩺 Possible Disease:", prediction)
print("⚠️ This is not a medical diagnosis. Please consult a doctor.")
