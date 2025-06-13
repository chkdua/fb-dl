from flask import Flask, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

# Direktori untuk menyimpan video sementara (opsional, jika ingin mengunduh)
# Jika Anda hanya ingin URL, tidak perlu direktori ini
DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

@app.route('/fb', methods=['GET'])
def download_video():
    video_url = request.args.get('url')

    if not video_url:
        return jsonify({"status": "error", "message": "Parameter 'url' tidak ditemukan."}), 400

    if not ("facebook.com" in video_url or "fb.watch" in video_url):
        return jsonify({"status": "error", "message": "URL bukan dari Facebook."}), 400

    try:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best', # Pilih format MP4 terbaik
            'noplaylist': True, # Pastikan tidak mengunduh playlist
            'quiet': True, # Jangan tampilkan output yt-dlp di console
            'no_warnings': True, # Jangan tampilkan peringatan
            'skip_download': True, # Hanya ekstrak informasi, jangan unduh
            'force_generic_extractor': True, # Coba ekstrak info bahkan jika situs tidak dikenali langsung
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=False) # Unduh=False untuk hanya mendapatkan metadata

            if not info_dict:
                return jsonify({"status": "error", "message": "Tidak dapat mengekstrak informasi video."}), 500

            # Cari URL download terbaik (misalnya, yang punya 'url' di 'formats')
            download_link = None
            title = info_dict.get('title', 'Unknown Title')
            thumbnail = info_dict.get('thumbnail')

            # Coba cari format yang memiliki URL langsung
            for f in info_dict.get('formats', []):
                if 'url' in f and 'ext' in f and f['ext'] == 'mp4': # Bisa diubah ke 'best' atau 'all'
                    download_link = f['url']
                    break
            
            # Jika tidak ditemukan di formats, kadang 'url' utama sudah ada
            if not download_link and 'url' in info_dict:
                 download_link = info_dict['url']

            if download_link:
                return jsonify({
                    "status": "success",
                    "title": title,
                    "download_url": download_link,
                    "thumbnail": thumbnail,
                    "extractor": info_dict.get('extractor'),
                    "duration": info_dict.get('duration'),
                    "upload_date": info_dict.get('upload_date')
                })
            else:
                return jsonify({"status": "error", "message": "Tidak dapat menemukan URL unduhan video yang valid."}), 500

    except yt_dlp.utils.DownloadError as e:
        return jsonify({"status": "error", "message": f"Terjadi kesalahan saat mengunduh: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": f"Terjadi kesalahan internal: {str(e)}"}), 500

if __name__ == '__main__':
    # Untuk lingkungan produksi, gunakan Gunicorn atau sejenisnya
    app.run(debug=True, host='0.0.0.0', port=5000)