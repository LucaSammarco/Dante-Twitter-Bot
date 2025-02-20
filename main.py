import sqlite3
import random
import tweepy
import os
import time
from datetime import datetime

# Database
db = sqlite3.connect("divina_commedia.sqlite")
cursor = db.cursor()
cursor.execute("SELECT id, nome FROM Cantica ORDER BY RANDOM() LIMIT 1")
cantica = cursor.fetchone()
if not cantica: exit()
cantica_id, cantica_nome = cantica
cursor.execute("SELECT id, numero, titolo FROM Canto WHERE id_cantica = ? ORDER BY RANDOM() LIMIT 1", (cantica_id,))
canto = cursor.fetchone()
if not canto: exit()
canto_id, _, canto_titolo = canto
cursor.execute("SELECT COUNT(*) FROM Verso WHERE id_canto = ?", (canto_id,))
num_verses = cursor.fetchone()[0]
if num_verses < 3: exit()
max_start = num_verses - 2
start_verse = random.randint(1, max_start)
total_left = num_verses - start_verse + 1
block_length = 3 if total_left != 4 else 4
cursor.execute("SELECT numero, testo FROM Verso WHERE id_canto = ? AND numero BETWEEN ? AND ? ORDER BY numero", 
               (canto_id, start_verse, start_verse + block_length - 1))
verses = cursor.fetchall()
verses_text = "\n".join(f"{row[0]} {row[1]}" for row in verses)
tweet_text = f"{cantica_nome}\n{canto_titolo}\n\n{verses_text}"
cursor.close()
db.close()

# Credenziali
api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
access_token = os.getenv("ACCESS_TOKEN")
access_secret = os.getenv("ACCESS_SECRET")
if not all([api_key, api_secret, access_token, access_secret]): 
    print("Errore: Credenziali mancanti")
    exit()

client = tweepy.Client(
    consumer_key=api_key,
    consumer_secret=api_secret,
    access_token=access_token,
    access_token_secret=access_secret
)

# Limite di sicurezza
DAILY_LIMIT = 15

# Contatore
COUNTER_FILE = "tweet_counter.txt"

def get_tweet_count():
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, "r") as f:
            data = f.read().strip().split(",")
            if len(data) == 2:
                count, last_date = int(data[0]), data[1]
                today = datetime.now().strftime("%Y-%m-%d")
                if last_date != today:
                    return 0, today
                return count, last_date
    return 0, datetime.now().strftime("%Y-%m-%d")

def update_tweet_count(count, date):
    with open(COUNTER_FILE, "w") as f:
        f.write(f"{count},{date}")

daily_count, last_date = get_tweet_count()

def publish_tweet(text):
    global daily_count, last_date
    if daily_count >= DAILY_LIMIT:
        print(f"Limite giornaliero raggiunto: {daily_count}/{DAILY_LIMIT}")
        return False
    try:
        response = client.create_tweet(text=text)
        daily_count += 1
        last_date = datetime.now().strftime("%Y-%m-%d")
        update_tweet_count(daily_count, last_date)
        print(f"Tweet pubblicato! ID: {response.data['id']} ({daily_count}/{DAILY_LIMIT})")
        return True
    except tweepy.errors.TooManyRequests as e:
        headers = e.response.headers
        reset_time = int(headers.get('x-rate-limit-reset'))
        wait_seconds = reset_time - int(time.time())
        if wait_seconds > 0:
            reset_datetime = datetime.fromtimestamp(reset_time)
            print(f"429: Attendo {wait_seconds} secondi fino a {reset_datetime}")
            time.sleep(wait_seconds)
            return publish_tweet(text)
        print("Reset passato, riprovo...")
        return publish_tweet(text)
    except Exception as e:
        print(f"Errore: {e}")
        return False

success = publish_tweet(tweet_text)
if not success:
    print("Impossibile pubblicare ora.")