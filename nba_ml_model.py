
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
import warnings
warnings.filterwarnings('ignore')

class NBAPredictor:
    """Machine Learning Modell für NBA-Spielvorhersagen"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = None
        self.accuracy = None
        
    def load_data(self, filename='nba_training_data.csv'):
        """Lädt die vorbereiteten Trainingsdaten"""
        df = pd.read_csv(filename)
        print(f"Daten geladen: {len(df)} Spiele")
        return df
    
    def prepare_features(self, df):
        """
        Wählt relevante Features aus und bereitet sie vor
        """
        # Feature-Spalten (ohne ID und Datum)
        feature_cols = [
            'TEAM1_HOME',
            'TEAM1_PTS_AVG', 'TEAM1_FG_PCT', 'TEAM1_FG3_PCT',
            'TEAM1_REB_AVG', 'TEAM1_AST_AVG', 'TEAM1_TOV_AVG',
            'TEAM2_PTS_AVG', 'TEAM2_FG_PCT', 'TEAM2_FG3_PCT',
            'TEAM2_REB_AVG', 'TEAM2_AST_AVG', 'TEAM2_TOV_AVG'
        ]
        
        # Entferne Zeilen mit fehlenden Werten
        df = df.dropna(subset=feature_cols + ['TEAM1_WON'])
        
        X = df[feature_cols]
        y = df['TEAM1_WON']
        
        self.feature_columns = feature_cols
        
        return X, y
    
    def train_model(self, X, y, test_size=0.2):
        """
        Trainiert das ML-Modell
        """
        # Split in Training und Test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, shuffle=True
        )
        
        print(f"\nTraining Set: {len(X_train)} Spiele")
        print(f"Test Set: {len(X_test)} Spiele")
        
        # Skaliere Features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Trainiere mehrere Modelle und wähle das beste
        print("\n=== Trainiere Modelle ===")
        
        # Random Forest
        rf_model = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_split=10,
            random_state=42,
            n_jobs=-1
        )
        rf_model.fit(X_train_scaled, y_train)
        rf_pred = rf_model.predict(X_test_scaled)
        rf_accuracy = accuracy_score(y_test, rf_pred)
        print(f"Random Forest Accuracy: {rf_accuracy:.2%}")
        
        # Gradient Boosting
        gb_model = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        gb_model.fit(X_train_scaled, y_train)
        gb_pred = gb_model.predict(X_test_scaled)
        gb_accuracy = accuracy_score(y_test, gb_pred)
        print(f"Gradient Boosting Accuracy: {gb_accuracy:.2%}")
        
        # Wähle bestes Modell
        if rf_accuracy > gb_accuracy:
            self.model = rf_model
            self.accuracy = rf_accuracy
            predictions = rf_pred
            print(f"\n✓ Random Forest ausgewählt (Accuracy: {rf_accuracy:.2%})")
        else:
            self.model = gb_model
            self.accuracy = gb_accuracy
            predictions = gb_pred
            print(f"\n✓ Gradient Boosting ausgewählt (Accuracy: {gb_accuracy:.2%})")
        
        # Detaillierte Metriken
        print("\n=== Classification Report ===")
        print(classification_report(y_test, predictions,
                                   target_names=['Team 2 Wins', 'Team 1 Wins']))
        
        # Feature Importance
        print("\n=== Top 5 wichtigste Features ===")
        feature_importance = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print(feature_importance.head())
        
        return X_test_scaled, y_test, predictions
    
    def predict_game(self, team1_stats, team2_stats, team1_home=True):
        """
        Vorhersage für ein einzelnes Spiel
        
        Args:
            team1_stats: Dict mit Stats von Team 1 (PTS_AVG, FG_PCT, etc.)
            team2_stats: Dict mit Stats von Team 2
            team1_home: Boolean, ob Team 1 Heimvorteil hat
        
        Returns:
            Dict mit Vorhersage und Wahrscheinlichkeiten
        """
        if self.model is None:
            raise ValueError("Modell muss erst trainiert werden!")
        
        # Erstelle Feature-Array
        features = np.array([[
            1 if team1_home else 0,
            team1_stats['PTS_AVG'],
            team1_stats['FG_PCT'],
            team1_stats['FG3_PCT'],
            team1_stats['REB_AVG'],
            team1_stats['AST_AVG'],
            team1_stats['TOV_AVG'],
            team2_stats['PTS_AVG'],
            team2_stats['FG_PCT'],
            team2_stats['FG3_PCT'],
            team2_stats['REB_AVG'],
            team2_stats['AST_AVG'],
            team2_stats['TOV_AVG']
        ]])
        
        # Skaliere Features
        features_scaled = self.scaler.transform(features)
        
        # Vorhersage
        prediction = self.model.predict(features_scaled)[0]
        probabilities = self.model.predict_proba(features_scaled)[0]
        
        result = {
            'winner': 'Team 1' if prediction == 1 else 'Team 2',
            'team1_win_probability': probabilities[1],
            'team2_win_probability': probabilities[0],
            'confidence': max(probabilities)
        }
        
        return result
    
    def save_model(self, filename='nba_model.pkl'):
        """Speichert trainiertes Modell"""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_columns': self.feature_columns,
            'accuracy': self.accuracy
        }
        joblib.dump(model_data, filename)
        print(f"\nModell gespeichert: {filename}")
    
    def load_model(self, filename='nba_model.pkl'):
        """Lädt gespeichertes Modell"""
        model_data = joblib.load(filename)
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_columns = model_data['feature_columns']
        self.accuracy = model_data['accuracy']
        print(f"Modell geladen (Accuracy: {self.accuracy:.2%})")


# Beispiel-Nutzung
if __name__ == "__main__":
    # Initialisiere Predictor
    predictor = NBAPredictor()
    
    # Lade Daten
    df = predictor.load_data('nba_training_data.csv')
    
    # Bereite Features vor
    X, y = predictor.prepare_features(df)
    
    # Trainiere Modell
    X_test, y_test, predictions = predictor.train_model(X, y)
    
    # Speichere Modell
    predictor.save_model()
    
    print("\n=== Beispiel-Vorhersage ===")
    
    # Beispiel: Lakers vs Warriors
    lakers_stats = {
        'PTS_AVG': 115.5,
        'FG_PCT': 0.475,
        'FG3_PCT': 0.365,
        'REB_AVG': 44.2,
        'AST_AVG': 26.8,
        'TOV_AVG': 13.5
    }
    
    warriors_stats = {
        'PTS_AVG': 118.2,
        'FG_PCT': 0.468,
        'FG3_PCT': 0.377,
        'REB_AVG': 42.8,
        'AST_AVG': 28.3,
        'TOV_AVG': 14.1
    }
    
    result = predictor.predict_game(lakers_stats, warriors_stats, team1_home=True)
    
    print(f"\nVorhersage: {result['winner']} gewinnt")
    print(f"Team 1 (Lakers) Gewinnchance: {result['team1_win_probability']:.1%}")
    print(f"Team 2 (Warriors) Gewinnchance: {result['team2_win_probability']:.1%}")
    print(f"Konfidenz: {result['confidence']:.1%}")
