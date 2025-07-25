# model/ai_model.py

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

def prepare_features(data: pd.DataFrame) -> pd.DataFrame:
    df = data.copy().dropna()

    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    df['Price_Change_%'] = df['Close'].pct_change() * 100
    df = df.dropna()

    features = df[['RSI', 'MACD', 'MACD_Signal', 'Price_Change_%']]
    labels = df['Target']
    
    return features, labels

def train_and_predict(data: pd.DataFrame) -> int:
    features, labels = prepare_features(data)

    X_train, X_test, y_train, y_test = train_test_split(
        features, labels, test_size=0.2, shuffle=False
    )

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    acc = accuracy_score(y_test, preds)
    print(f"Model Accuracy: {round(acc * 100, 2)}%")

    latest_features = features.iloc[[-1]]
    prediction = model.predict(latest_features)[0]
    return prediction
