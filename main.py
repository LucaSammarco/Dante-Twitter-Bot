import sqlite3
import random
import tweepy
import os

# Connessione al database SQLite
db = sqlite3.connect("divina_commedia.sqlite")
cursor = db.cursor()

# Seleziona una cantica casuale
cursor.execute("SELECT id, nome FROM Cantica ORDER BY RANDOM() LIMIT 1")
cantica = cursor.fetchone()
if not cantica:
    exit()
cantica_id, cantica_nome = cantica

# Seleziona un canto casuale appartenente alla cantica scelta
cursor.execute("SELECT id, numero, titolo FROM Canto WHERE id_cantica = ? ORDER BY RANDOM() LIMIT 1", (cantica_id,))
canto = cursor.fetchone()
if not canto:
    exit()
canto_id, _, canto_titolo = canto

# Conta il numero totale dei versi nel canto selezionato
cursor.execute("SELECT COUNT(*) FROM Verso WHERE id_canto = ?", (canto_id,))
num_verses = cursor.fetchone()[0]
if num_verses < 3:
    exit()

# Determina il verso di partenza garantendo almeno 3 versi consecutivi
max_start = num_verses - 2
start_verse = random.randint(1, max_start)

# Calcola quanti versi rimangono dal verso scelto e imposta il blocco
total_left = num_verses - start_verse + 1
block_length = 3
if total_left == 4:
    block_length = 4

# Estrae i versi (numero e testo) ordinati per numero
cursor.execute("SELECT numero, testo FROM Verso WHERE id_canto = ? AND numero BETWEEN ? AND ? ORDER BY numero", 
               (canto_id, start_verse, start_verse + block_length - 1))
verses = cursor.fetchall()

# Crea il testo formattato per ogni verso senza il punto dopo il numero
verses_text = "\n".join(f"{row[0]} {row[1]}" for row in verses)

# Costruisce il testo finale includendo la cantica e il canto
tweet_text = f"{cantica_nome}\n{canto_titolo}\n\n{verses_text}"

# Chiude la connessione al database
cursor.close()
db.close()

# Recupera le credenziali Twitter dagli environment variables (se configurato correttamente in GitHub Actions)
api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
access_token = os.getenv("ACCESS_TOKEN")
access_secret = os.getenv("ACCESS_SECRET")

# Verifica che tutte le credenziali siano state trovate
if not all([api_key, api_secret, access_token, access_secret]):
    print("Errore: credenziali Twitter non trovate nelle variabili d'ambiente!")
    exit()

# Crea il client Tweepy per interagire con l'API Twitter v2
client = tweepy.Client(bearer_token=None,
                       consumer_key=api_key,
                       consumer_secret=api_secret,
                       access_token=access_token,
                       access_token_secret=access_secret)

# Pubblica il tweet con il testo costruito
response = client.create_tweet(text=tweet_text)
print("Tweet pubblicato con successo! ID:", response.data["id"])
