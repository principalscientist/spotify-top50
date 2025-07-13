import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd

# --- Spotify API credentials ---
CLIENT_ID = 'FILL IN' # Must match Spotify app settings
CLIENT_SECRET = 'FILL IN' # Must match Spotify app settings
REDIRECT_URI = 'https://example.com/callback'  # Must match Spotify app settings

scope = 'user-top-read'

# --- Authenticate with Spotify ---
sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=scope,
    open_browser=True
)

token_info = sp_oauth.get_access_token(as_dict=False)
if not token_info:
    auth_url = sp_oauth.get_authorize_url()
    print("Please navigate here:", auth_url)
    response = input("Paste the full redirect URL after login: ")
    code = sp_oauth.parse_response_code(response)
    token_info = sp_oauth.get_access_token(code)

sp = spotipy.Spotify(auth=token_info)

# --- Get user's top 50 tracks ---
print("Fetching top tracks...")
results = sp.current_user_top_tracks(limit=50, time_range='long_term')

tracks = []
artist_ids = set()

# Gather basic track info + artist IDs
for item in results['items']:
    artist_id = item['artists'][0]['id'] if item.get('artists') else None
    artist_ids.add(artist_id)
    tracks.append({
        'track_name': item['name'],
        'artist_id': artist_id,
        'artist': item['artists'][0]['name'],
        'album': item['album']['name'],
        'popularity': item['popularity'],
        'duration_ms': item['duration_ms'],
        'duration_min': item['duration_ms'] / 60000,
        'explicit': item['explicit'],
        'track_id': item['id'],
        'spotify_url': item['external_urls']['spotify'],
        'track_number': item['track_number'],
        'disc_number': item['disc_number'],
        'available_markets_count': len(item['available_markets']),
    })

# --- Fetch artist info in batches ---
print("Fetching artist details...")
artist_ids = list(filter(None, artist_ids))  # remove None if any
artists_info = {}

for i in range(0, len(artist_ids), 50):  # Spotify max batch = 50
    batch_ids = artist_ids[i:i+50]
    response = sp.artists(batch_ids)
    for artist in response['artists']:
        artists_info[artist['id']] = {
            'artist_genres': ', '.join(artist.get('genres', [])),
            'artist_followers': artist.get('followers', {}).get('total'),
            'artist_popularity': artist.get('popularity')
        }

# --- Merge artist info into tracks ---
for track in tracks:
    artist_id = track['artist_id']
    artist_data = artists_info.get(artist_id, {})
    track['artist_genres'] = artist_data.get('artist_genres')
    track['artist_followers'] = artist_data.get('artist_followers')
    track['artist_popularity'] = artist_data.get('artist_popularity')

# --- Save to CSV ---
df = pd.DataFrame(tracks)
csv_file = 'spotify_top_tracks_with_artist_info.csv'
df.to_csv(csv_file, index=False)
print(f"✅ CSV saved as {csv_file}")

