import pandas as pd
import numpy as np
from nba_api.stats.endpoints import leaguegamefinder, teamgamelogs
from nba_api.stats.static import teams
from datetime import datetime, timedelta
import time

class NBADataCollector:
    """Sammelt NBA-Spieldaten für Machine Learning"""
    
    def __init__(self):
        self.all_teams = teams.get_teams()
        
    def get_team_id(self, team_name):
        """Findet Team ID anhand des Namens"""
        for team in self.all_teams:
            if team_name.lower() in team['full_name'].lower():
                return team['id']
        return None
    
    def collect_season_games(self, season='2023-24', max_retries=3):
        """
        Sammelt alle Spiele einer Saison
        Season Format: '2023-24'
        """
        print(f"Sammle Daten für Saison {season}...")
        
        for attempt in range(max_retries):
            try:
                # Hole alle Spiele der Saison mit Timeout
                print(f"Versuch {attempt + 1}/{max_retries}...")
                gamefinder = leaguegamefinder.LeagueGameFinder(
                    season_nullable=season,
                    league_id_nullable='00',
                    timeout=60
                )
                
                games = gamefinder.get_data_frames()[0]
                
                # Filtere nur reguläre Season (ohne Playoffs)
                games = games[games['SEASON_ID'].str.contains('2')]
                
                print(f"✓ Gefunden: {len(games)} Spiel-Einträge")
                return games
                
            except Exception as e:
                print(f"✗ Fehler beim Versuch {attempt + 1}: {str(e)[:100]}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 10
                    print(f"Warte {wait_time} Sekunden und versuche erneut...")
                    time.sleep(wait_time)
                else:
                    print("\n⚠ Konnte keine Daten laden. Alternativen:")
                    print("1. Versuche eine ältere Saison: '2022-23' oder '2021-22'")
                    print("2. Warte 5 Minuten und versuche es nochmal")
                    print("3. Nutze die Beispiel-Daten (siehe unten)\n")
                    raise
    
    def prepare_training_data(self, games_df):
        """
        Bereitet Daten für ML vor
        Erstellt Features wie: Team Stats, Rolling Averages, Home/Away
        """
        # Sortiere nach Datum
        games_df['GAME_DATE'] = pd.to_datetime(games_df['GAME_DATE'])
        games_df = games_df.sort_values('GAME_DATE')
        
        # Erstelle Win/Loss als numerische Variable
        games_df['WON'] = (games_df['WL'] == 'W').astype(int)
        
        # Berechne Rolling Averages (letzte 5 Spiele)
        games_df = games_df.sort_values(['TEAM_ID', 'GAME_DATE'])
        
        rolling_cols = ['PTS', 'FG_PCT', 'FG3_PCT', 'FT_PCT', 'REB', 'AST', 'STL', 'BLK', 'TOV']
        
        for col in rolling_cols:
            games_df[f'{col}_ROLLING_5'] = games_df.groupby('TEAM_ID')[col].transform(
                lambda x: x.rolling(window=5, min_periods=1).mean()
            )
        
        # Home/Away Indikator (@ bedeutet Away Game)
        games_df['IS_HOME'] = (~games_df['MATCHUP'].str.contains('@')).astype(int)
        
        return games_df
    
    def create_matchup_dataset(self, games_df):
        """
        Erstellt Dataset mit beiden Teams pro Spiel
        Format: Team A Stats | Team B Stats | Winner
        """
        # Gruppiere nach Game ID (jedes Spiel hat 2 Einträge - ein Team pro Zeile)
        matchups = []
        
        for game_id in games_df['GAME_ID'].unique():
            game_data = games_df[games_df['GAME_ID'] == game_id]
            
            if len(game_data) != 2:
                continue  # Überspringe inkomplette Spiele
            
            team1 = game_data.iloc[0]
            team2 = game_data.iloc[1]
            
            # Features für Team 1
            matchup = {
                'GAME_DATE': team1['GAME_DATE'],
                'TEAM1_ID': team1['TEAM_ID'],
                'TEAM2_ID': team2['TEAM_ID'],
                'TEAM1_HOME': team1['IS_HOME'],
                'TEAM1_PTS_AVG': team1['PTS_ROLLING_5'],
                'TEAM1_FG_PCT': team1['FG_PCT_ROLLING_5'],
                'TEAM1_FG3_PCT': team1['FG3_PCT_ROLLING_5'],
                'TEAM1_REB_AVG': team1['REB_ROLLING_5'],
                'TEAM1_AST_AVG': team1['AST_ROLLING_5'],
                'TEAM1_TOV_AVG': team1['TOV_ROLLING_5'],
                'TEAM2_PTS_AVG': team2['PTS_ROLLING_5'],
                'TEAM2_FG_PCT': team2['FG_PCT_ROLLING_5'],
                'TEAM2_FG3_PCT': team2['FG3_PCT_ROLLING_5'],
                'TEAM2_REB_AVG': team2['REB_ROLLING_5'],
                'TEAM2_AST_AVG': team2['AST_ROLLING_5'],
                'TEAM2_TOV_AVG': team2['TOV_ROLLING_5'],
                'TEAM1_WON': team1['WON']
            }
            
            matchups.append(matchup)
            
            time.sleep(0.1)  # Rate limiting
        
        matchups_df = pd.DataFrame(matchups)
        print(f"Erstellt: {len(matchups_df)} Matchup-Datensätze")
        
        return matchups_df
    
    def save_data(self, df, filename='nba_training_data.csv'):
        """Speichert Daten als CSV"""
        df.to_csv(filename, index=False)
        print(f"Daten gespeichert: {filename}")


# Beispiel-Nutzung
if __name__ == "__main__":
    collector = NBADataCollector()
    
    # Versuche zuerst aktuelle Saison, dann ältere
    seasons_to_try = ['2023-24', '2022-23', '2021-22']
    
    games = None
    for season in seasons_to_try:
        try:
            print(f"\n=== Versuche Saison {season} ===")
            games = collector.collect_season_games(season)
            break
        except Exception as e:
            print(f"Saison {season} fehlgeschlagen")
            continue
    
    if games is None:
        print("\n❌ Konnte keine Daten laden.")
        print("📁 Alternative: Nutze vorbereitete Demo-Daten")
        print("Kontaktiere mich für Demo-Daten oder versuche es später nochmal.")
        exit(1)
    
    # Bereite Daten vor
    prepared_games = collector.prepare_training_data(games)
    
    # Erstelle Matchup-Dataset
    matchups = collector.create_matchup_dataset(prepared_games)
    
    # Speichere für Training
    collector.save_data(matchups)
    
    print("\n=== ✓ Datensammlung abgeschlossen ===")
    print(f"Anzahl Spiele: {len(matchups)}")
    print(f"\nBeispiel-Daten:")
    print(matchups.head())
