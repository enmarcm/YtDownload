import yt_dlp
import os

def descargar_con_ytdlp(url):
    # Primero, obtenemos información para saber si es playlist
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        info = ydl.extract_info(url, download=False)
        is_playlist = 'entries' in info
        playlist_title = info.get('title', '') if is_playlist else None

    # Construimos la ruta de salida
    if is_playlist:
        outtmpl = os.path.join('downloads', playlist_title, '%(title)s.%(ext)s')
    else:
        outtmpl = os.path.join('downloads', '%(title)s.%(ext)s')

    ydl_opts = {
        'format': 'bestvideo[ext=mp4][height<=720][acodec!=none][vcodec!=none]+bestaudio[ext=m4a]/best[ext=mp4][height<=720]/best[height<=720]',
        'outtmpl': outtmpl,
        'noplaylist': False,  # Permite descargar playlists completas
        'quiet': False,
        'merge_output_format': 'mp4'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
        except Exception as e:
            print(f"Error al descargar {url}: {e}")

def main():
    with open('datos.txt', 'r', encoding='utf-8') as archivo:
        enlaces = [linea.strip() for linea in archivo if linea.strip()]
    for enlace in enlaces:
        descargar_con_ytdlp(enlace)

if __name__ == "__main__":
    main()