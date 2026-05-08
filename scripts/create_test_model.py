from sklearn.linear_model import LogisticRegression
import numpy as np
import joblib

X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
y = np.array([0, 0, 1, 1])

model = LogisticRegression()
model.fit(X, y)

joblib.dump(model, "test_model.pkl")
print("Модель сохранена: test_model.pkl")