import boto3
from scrape_all_data import scrape_lineup_stats, scrape_lineup_shots, scrape_player_shots

s3 = boto3.client("s3")
BUCKET = "netstats-data"

def upload_file(local_path, s3_key):
    s3.upload_file(local_path, BUCKET, s3_key)

if __name__ == "__main__":
    data = scrape_lineup_stats()
    scrape_lineup_shots(data)
    scrape_player_shots()

    for filename in os.listdir("network_data"):
        if filename.endswith(".json"):
            upload_file(f"network_data/{filename}", filename)
            print(f"✅ Uploaded {filename}")