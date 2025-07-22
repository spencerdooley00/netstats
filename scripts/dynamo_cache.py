import boto3
from boto3.dynamodb.conditions import Key

REGION = "us-east-2"
dynamodb = boto3.resource("dynamodb", region_name=REGION)

# --- Direct DynamoDB Query Functions ---

def get_all_stats(season, team):
    key = f"{season}-{team}"
    table = dynamodb.Table("AllStats")
    response = table.query(KeyConditionExpression=Key("id").eq(key))

    items = response.get("Items", [])
    if not items:
        return {}

    players_dict = items[0].get("players", {})
    return players_dict  # already in {player_name: data} format
def get_player_shots(season, team, player):
    key = f"{season}-{team}-{player}"
    table = dynamodb.Table("PlayerShots")
    response = table.get_item(Key={"id": key})
    return response.get("Item", {}).get("shots", [])

def get_lineup_shots(season, team, lineup_id):
    key = f"{season}-{team}-{lineup_id}"
    table = dynamodb.Table("LineupShots")
    response = table.get_item(Key={"id": key})
    return response.get("Item", {}).get("shots", [])

def get_top_lineups(season, team):
    key = f"{season}-{team}"
    table = dynamodb.Table("TopLineups")
    response = table.query(KeyConditionExpression=Key("id").eq(key))
    return response.get("Items", [])

def get_assist_data(season, team, lineup_id):
    key = f"{season}-{team}"
    table = dynamodb.Table("AssistData")
    response = table.get_item(Key={"id": key})
    return response.get("Item", {})['lineups'][lineup_id]
