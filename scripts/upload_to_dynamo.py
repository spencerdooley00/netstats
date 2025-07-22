import boto3
import json
from botocore.exceptions import ClientError
from decimal import Decimal

REGION = "us-east-2"
BUCKET_NAME = "netstats-data"

dynamodb = boto3.resource("dynamodb", region_name=REGION)
s3 = boto3.client("s3")
client = boto3.client("dynamodb", region_name=REGION)

files_to_tables = {
    "all_stats_test.json": "AllStats",
    "conditional_assist_networks_new_id.json": "AssistData",
    "lineup_shots.json": "LineupShots",
    "player_shots.json": "PlayerShots",
    "teams.json": "Teams",
    "top_lineups.json": "TopLineups"
}

files_to_update = []
def create_table_if_not_exists(table_name, primary_key="id"):
    if table_name in client.list_tables()["TableNames"]:
        print(f"✅ Table {table_name} already exists.")
        return
    print(f"🚀 Creating table: {table_name}")
    client.create_table(
        TableName=table_name,
        KeySchema=[{"AttributeName": primary_key, "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": primary_key, "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST"
    )
    client.get_waiter("table_exists").wait(TableName=table_name)
    print(f"✅ Table {table_name} created and ready.")

def load_json_from_s3(key):
    obj = s3.get_object(Bucket=BUCKET_NAME, Key=key)
    return json.load(obj["Body"], parse_float=Decimal)

# New optimized transformers

def transform_all_stats(data):
    for season, teams in data.items():
        for team, players in teams.items():
            key = f"{season}-{team}"
            yield {
                "id": key,
                "season": season,
                "team": team,
                "players": players
            }

def transform_assist_data(data):
    for season, teams in data.items():
        for team, lineup_data in teams.items():
            yield {
                "id": f"{season}-{team}",
                "season": season,
                "team": team,
                "lineups": lineup_data
            }

def transform_lineup_shots(data):
    for season, teams in data.items():
        for team, lineups in teams.items():
            for lineup_id, shots in lineups.items():
                yield {
                    "id": f"{season}-{team}-{lineup_id}",
                    "season": season,
                    "team": team,
                    "lineup_id": lineup_id,
                    "shots": shots
                }

def transform_player_shots(data):
    for season, teams in data.items():
        for team, players in teams.items():
            for player, shots in players.items():
                yield {
                    "id": f"{season}-{team}-{player}",
                    "season": season,
                    "team": team,
                    "player": player,
                    "shots": shots
                }

def transform_teams(data):
    for season_key, teams in data.items():
        for abbr, meta in teams.items():
            yield {
                "id": f"{season_key}-{abbr}",
                "season": season_key,
                "team": abbr,
                **meta
            }

def transform_top_lineups(data):
    for season, teams in data.items():
        for team, lineups in teams.items():
            yield {
                "id": f"{season}-{team}",
                "season": season,
                "team": team,
                "lineups": lineups
            }

transformers = {
    "all_stats_test.json": transform_all_stats,
    "conditional_assist_networks_new_id.json": transform_assist_data,
    "lineup_shots.json": transform_lineup_shots,
    "player_shots.json": transform_player_shots,
    "teams.json": transform_teams,
    "top_lineups.json": transform_top_lineups
}

def upload_to_dynamodb(table_name, data, transform_fn):
    table = dynamodb.Table(table_name)
    count = 0
    for item in transform_fn(data):
        try:
            table.put_item(Item=item)
            count += 1
            if count % 50 == 0:
                print(f"...{count} items uploaded to {table_name}")
        except ClientError as e:
            print(f"❌ Error uploading to {table_name}: {e}")
    print(f"✅ Done uploading {count} items to {table_name}")

# Upload loop
for file, table in files_to_tables.items():
    create_table_if_not_exists(table)
    data = load_json_from_s3(file)
    upload_to_dynamodb(table, data, transformers[file])
