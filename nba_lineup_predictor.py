import json
import numpy as np
from nba_synergy_system import TeamSynergyCalculator

class NBALineupPredictor:
    """
    Advanced NBA Predictor basierend auf Spieler-Lineups mit Synergien
    """
    
    def __init__(self):
        self.synergy_calc = TeamSynergyCalculator()
        self.players = self.synergy_calc.players
        
    def predict_game(self, lineup1_names, lineup2_names, team1_home=True):
        """
        Macht Vorhersage basierend auf zwei 5-Spieler-Lineups
        """
        # Vergleiche Lineups
        comparison = self.synergy_calc.compare_lineups(lineup1_names, lineup2_names)
        
        if not comparison:
            return None
        
        team1 = comparison['team1']
        team2 = comparison['team2']
        
        # === SCORING PREDICTION ===
        # Basis: Durchschnittliche Punkte der Spieler
        team1_base_pts = team1['stats']['PTS']
        team2_base_pts = team2['stats']['PTS']
        
        # Synergy-Multiplikatoren
        team1_synergy_mult = 1 + (team1['synergies']['total'] / 500)
        team2_synergy_mult = 1 + (team2['synergies']['total'] / 500)
        
        # Effizienz-Faktor (FG%)
        team1_efficiency = team1['stats']['FG_PCT']
        team2_efficiency = team2['stats']['FG_PCT']
        
        # Predicted Scores
        team1_predicted_pts = team1_base_pts * team1_synergy_mult * (0.9 + team1_efficiency * 0.2)
        team2_predicted_pts = team2_base_pts * team2_synergy_mult * (0.9 + team2_efficiency * 0.2)
        
        # Heimvorteil
        if team1_home:
            team1_predicted_pts += 3.5
        else:
            team2_predicted_pts += 3.5
        
        # Defense-Anpassung
        team1_defense_factor = team1['synergies']['defense'] / 100
        team2_defense_factor = team2['synergies']['defense'] / 100
        
        team1_predicted_pts = team1_predicted_pts * (1 - team2_defense_factor * 0.1)
        team2_predicted_pts = team2_predicted_pts * (1 - team1_defense_factor * 0.1)
        
        # === WIN PROBABILITY ===
        score_diff = team1_predicted_pts - team2_predicted_pts
        synergy_diff = team1['synergies']['total'] - team2['synergies']['total']
        
        total_advantage = score_diff * 2 + synergy_diff / 10
        
        # Sigmoid für Wahrscheinlichkeit
        team1_win_prob = 1 / (1 + np.exp(-total_advantage / 10))
        team2_win_prob = 1 - team1_win_prob
        
        return {
            'team1_score': round(team1_predicted_pts),
            'team2_score': round(team2_predicted_pts),
            'team1_win_prob': team1_win_prob,
            'team2_win_prob': team2_win_prob,
            'winner': 1 if team1_predicted_pts > team2_predicted_pts else 2,
            'confidence': max(team1_win_prob, team2_win_prob),
            'comparison': comparison
        }
    
    def print_prediction(self, result, team1_name="Team 1", team2_name="Team 2"):
        """
        Zeigt detaillierte Vorhersage
        """
        if not result:
            return
        
        comp = result['comparison']
        
        print("\n" + "="*70)
        print("🏀 LINEUP-BASIERTE VORHERSAGE")
        print("="*70)
        
        # Lineups
        print(f"\n🏠 {team1_name} Starting 5:")
        for player in comp['team1']['lineup']:
            player_data = self.players[player]
            pts = player_data['stats'].get('PTS', 0)
            ptype = player_data['type']
            print(f"   - {player:25} ({pts:.1f} PPG, {ptype})")
        
        print(f"\n✈️  {team2_name} Starting 5:")
        for player in comp['team2']['lineup']:
            player_data = self.players[player]
            pts = player_data['stats'].get('PTS', 0)
            ptype = player_data['type']
            print(f"   - {player:25} ({pts:.1f} PPG, {ptype})")
        
        # Predicted Score
        print("\n" + "="*70)
        print("📊 VORHERGESAGTER ENDSTAND")
        print("="*70)
        print(f"\n   {team1_name}: {result['team1_score']}")
        print(f"   {team2_name}: {result['team2_score']}")
        
        winner_name = team1_name if result['winner'] == 1 else team2_name
        print(f"\n🏆 Gewinner: {winner_name}")
        
        # Wahrscheinlichkeiten
        print("\n" + "="*70)
        print("📈 GEWINNWAHRSCHEINLICHKEITEN")
        print("="*70)
        print(f"\n   {team1_name}: {result['team1_win_prob']*100:.1f}%")
        print(f"   {team2_name}: {result['team2_win_prob']*100:.1f}%")
        
        confidence = result['confidence'] * 100
        print(f"\n🎯 Konfidenz: {confidence:.1f}%")
        
        if confidence > 70:
            print("   ✓ Hohe Konfidenz - Klarer Favorit")
        elif confidence > 60:
            print("   → Moderate Konfidenz - Leichter Favorit")
        else:
            print("   ⚠ Niedrige Konfidenz - Ausgeglichenes Spiel")
        
        # Synergy Analysis
        print("\n" + "="*70)
        print("🔥 SYNERGY-ANALYSE")
        print("="*70)
        
        team1_syn = comp['team1']['synergies']
        team2_syn = comp['team2']['synergies']
        
        synergy_categories = [
            ('spacing', '3-Point Spacing'),
            ('playmaking', 'Playmaking'),
            ('rebounding', 'Rebounding'),
            ('defense', 'Defense'),
            ('ball_movement', 'Ball Movement'),
            ('balance', 'Scoring Balance')
        ]
        
        print(f"\n{'Kategorie':<20} {team1_name:<15} {team2_name:<15} Vorteil")
        print("-" * 70)
        
        for key, label in synergy_categories:
            t1_val = team1_syn[key]
            t2_val = team2_syn[key]
            
            if t1_val > t2_val:
                advantage = f"✓ {team1_name}"
            elif t2_val > t1_val:
                advantage = f"✓ {team2_name}"
            else:
                advantage = "="
            
            print(f"{label:<20} {t1_val:<15.1f} {t2_val:<15.1f} {advantage}")
        
        print("-" * 70)
        print(f"{'TOTAL':<20} {team1_syn['total']:<15.1f} {team2_syn['total']:<15.1f}")
        
        # Key Insights
        print("\n" + "="*70)
        print("💡 KEY INSIGHTS")
        print("="*70)
        
        # Offense
        if comp['team1']['stats']['PTS'] > comp['team2']['stats']['PTS']:
            diff = comp['team1']['stats']['PTS'] - comp['team2']['stats']['PTS']
            print(f"\n✓ {team1_name} hat mehr Scoring-Power (+{diff:.1f} PPG)")
        else:
            diff = comp['team2']['stats']['PTS'] - comp['team1']['stats']['PTS']
            print(f"\n✓ {team2_name} hat mehr Scoring-Power (+{diff:.1f} PPG)")
        
        # Synergien
        if team1_syn['total'] > team2_syn['total']:
            diff = team1_syn['total'] - team2_syn['total']
            print(f"✓ {team1_name} hat bessere Team-Chemie (Synergy: +{diff:.1f})")
        else:
            diff = team2_syn['total'] - team1_syn['total']
            print(f"✓ {team2_name} hat bessere Team-Chemie (Synergy: +{diff:.1f})")
        
        # Defense
        if team1_syn['defense'] > team2_syn['defense']:
            print(f"✓ {team1_name} hat die bessere Defense")
        else:
            print(f"✓ {team2_name} hat die bessere Defense")
        
        # Playmaking
        if team1_syn['playmaking'] > team2_syn['playmaking']:
            print(f"✓ {team1_name} hat besseres Playmaking")
        else:
            print(f"✓ {team2_name} hat besseres Playmaking")
        
        print("\n" + "="*70)
    
    def interactive_mode(self):
        """
        Interaktiver Modus - Spieler auswählen
        """
        print("\n" + "="*70)
        print("🏀 NBA LINEUP PREDICTOR - INTERACTIVE MODE")
        print("="*70)
        print(f"\nVerfügbare Spieler: {len(self.players)}")
        print("\nTipp: Gib Spielernamen ein (z.B. 'LeBron James')")
        print("      Oder 'list' um alle Spieler zu sehen\n")
        
        def get_lineup(team_name):
            lineup = []
            print(f"\n{team_name} - Wähle 5 Spieler:")
            
            for i in range(5):
                while True:
                    player_input = input(f"  Spieler {i+1}: ").strip()
                    
                    if player_input.lower() == 'list':
                        print("\nVerfügbare Spieler:")
                        for idx, name in enumerate(sorted(self.players.keys())[:50], 1):
                            print(f"  {name}")
                        print(f"\n... und {len(self.players) - 50} weitere")
                        continue
                    
                    # Suche Spieler
                    found = None
                    for name in self.players.keys():
                        if player_input.lower() in name.lower():
                            found = name
                            break
                    
                    if found:
                        if found in lineup:
                            print(f"  ⚠ {found} ist bereits im Lineup!")
                            continue
                        lineup.append(found)
                        player_data = self.players[found]
                        print(f"  ✓ {found} ({player_data['stats'].get('PTS', 0):.1f} PPG)")
                        break
                    else:
                        print(f"  ❌ Spieler '{player_input}' nicht gefunden. Versuche es nochmal.")
            
            return lineup
        
        # Team 1
        team1_lineup = get_lineup("🏠 TEAM 1 (Heim)")
        
        # Team 2
        team2_lineup = get_lineup("✈️  TEAM 2 (Auswärts)")
        
        # Prediction
        print("\n⏳ Berechne Vorhersage mit Synergien...")
        result = self.predict_game(team1_lineup, team2_lineup, team1_home=True)
        
        if result:
            self.print_prediction(result, "TEAM 1", "TEAM 2")
        
        # Nochmal?
        print("\n" + "-"*70)
        again = input("\nWeitere Vorhersage? (j/n): ").strip().lower()
        if again == 'j':
            self.interactive_mode()
        else:
            print("\n👋 Viel Erfolg! 🏀\n")


# Beispiel-Nutzung
if __name__ == "__main__":
    predictor = NBALineupPredictor()
    
    # Teste mit vordefinierten Lineups
    print("Teste mit Beispiel-Lineups...\n")
    
    lakers = [
        'LeBron James',
        'Anthony Davis',
        'Austin Reaves',
        'Rui Hachimura',
        "D'Angelo Russell"
    ]
    
    warriors = [
        'Stephen Curry',
        'Andrew Wiggins',
        'Draymond Green',
        'Trayce Jackson-Davis',
        'Gary Payton II'
    ]
    
    result = predictor.predict_game(lakers, warriors, team1_home=True)
    if result:
        predictor.print_prediction(result, "Lakers", "Warriors")
    
    # Starte interaktiven Modus
    print("\n" + "="*70)
    start = input("\nInteraktiven Modus starten? (j/n): ").strip().lower()
    if start == 'j':
        predictor.interactive_mode()
