import sqlite3
import pandas as pd

# Connect to the SQLite database
conn = sqlite3.connect("acc1819.db")
print("Connected to database")

# Load games and box_scores tables
games = pd.read_sql("SELECT * FROM games;", conn)
box_scores = pd.read_sql("SELECT * FROM box_scores;", conn)

# Merge box scores with game information
df = box_scores.merge(games, on="GameId", how="left")

# Create a column for the opponent team in each game
df["Opponent"] = df.groupby("GameId")["Team"].transform(lambda x: x.iloc[::-1].values)

# Compute opponent score for each game
df["OpponentScore"] = df.groupby("GameId")["Score"].transform("sum") - df["Score"]

# Compute raw point margin for each team in each game
df["PointMargin"] = df["Score"] - df["OpponentScore"]

# Function to assign weights for home, away, and neutral games
def location_weight(home_flag):
    if home_flag == 1:
        return 0.95   # home game slightly discounted
    elif home_flag == 0:
        return 1.05   # away game slightly boosted
    else:
        return 1.00   # neutral site unchanged

# Apply location weights to create a weighted margin
df["LocationWeight"] = df["Home"].apply(location_weight)
df["AdjPointMargin"] = df["PointMargin"] * df["LocationWeight"]

# Compute each team's average adjusted margin across all games
team_margin = df.groupby("Team")["AdjPointMargin"].mean().rename("AvgAdjMargin")

# Map opponent average margin to each game for strength of schedule
df["OpponentAvgMargin"] = df["Opponent"].map(team_margin)

# Compute each team's strength of schedule as the average of opponents' adjusted margins
sos = df.groupby("Team")["OpponentAvgMargin"].mean().rename("SoS")

# Combine average adjusted margin and strength of schedule into a final rating
final = pd.concat([team_margin, sos], axis=1).reset_index()
final["Rating"] = 0.7 * final["AvgAdjMargin"] + 0.3 * final["SoS"]

# Rank teams from best to worst based on final rating
final = final.sort_values("Rating", ascending=False).reset_index(drop=True)
final["Rank"] = final.index + 1

# Select columns in the desired output format
final_rankings = final[["Rank", "Team", "Rating"]]

# Export final rankings to CSV
final_rankings.to_csv("ACCRankings1819.csv", index=False)

print("\nFinal ACC Rankings with Home/Away Weighting:")
print(final_rankings)

