import os
import csv
from pytube import YouTube
from pytube.exceptions import RegexMatchError
from youtube_search import YoutubeSearch
import os
import re
import spotipy
from spotipy.oauth2 import SpotifyOAuth

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Spotify API credentials
client_id = '67968b590a1842a4b66e3876d334d1e9'
client_secret = 'c96393b55ebf4b02a6a99891a077348a'

# Set up Spotify API access
scope = "user-library-read"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri='http://localhost:8888/callback', scope=scope))

# Function to search for a song on YouTube and return the video URL
def search_youtube(song_name, artist):
    query = f"{song_name} {artist} audio"
    results = YoutubeSearch(query, max_results=1).to_dict()
    if results:
        return f"https://www.youtube.com{results[0]['url_suffix']}"
    else:
        return None

# Function to download music from YouTube URL
def download_music(url, output_path, downloaded_songs_csv):
    try:
        yt = YouTube(url)
        audio_stream = yt.streams.filter(only_audio=True).first()
        
        # Rename the file to match the song name
        new_filename = re.sub(r'[^\w\s.-]', '', audio_stream.title) + ".mp3"
        new_filename = new_filename[:255]  # Truncate file name if it exceeds 255 characters (Windows limit)
        
        if new_filename not in downloaded_songs_csv:
            audio_stream.download(output_path)
            downloaded_songs_csv.append(new_filename)
            write_downloaded_songs_csv([new_filename])  # Update the downloaded files CSV for each downloaded song
            print(f"Download complete: {new_filename}")
            return True
        else:
            print(f"Skipping download of {new_filename}: Already downloaded.")
            return False
    except RegexMatchError:
        print(f"Error downloading {url}: Video not available")
        return False

# Function to write downloaded song details to CSV
def write_downloaded_songs_csv(downloaded_songs):
    with open("downloaded_songs.csv", mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for song in downloaded_songs:
            writer.writerow([song])

if __name__ == "__main__":
    # Get the user's liked songs from Spotify
    liked_songs = []
    offset = 0
    while True:
        tracks = sp.current_user_saved_tracks(limit=50, offset=offset)
        if not tracks['items']:
            break
        for item in tracks['items']:
            track = item['track']
            liked_songs.append({'Name': track['name'], 'Artist': track['artists'][0]['name']})
        offset += 50

    # Modify the output path where you want to save the downloaded mp3 files
    output_path = "./downloaded_music"

    # Read the list of downloaded songs from the CSV file
    downloaded_songs_csv = []
    if os.path.exists("downloaded_songs.csv"):
        with open("downloaded_songs.csv", mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            downloaded_songs_csv = [row[0] for row in reader]

    # Iterate through each song and attempt to download it
    for song in liked_songs:
        name = song['Name']
        artist = song['Artist']
        print(f"Downloading: {name} - {artist}")

        # Search for the song on YouTube
        url = search_youtube(name, artist)
        if url:
            # Download the song if a YouTube URL is found
            download_music(url, output_path, downloaded_songs_csv)
        else:
            print("Song not found on YouTube.")
