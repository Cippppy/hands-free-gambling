from flask import Flask, render_template_string, request
import subprocess
import random
import os
import sys

app = Flask(__name__)

# Base layout with Bootstrap and voice input
base_header = """
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <title>Barbie Auto</title>
    <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
    <style>
        body { padding-top: 70px; }
        #mic-btn {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 999;
        }
    </style>
</head>
<body>
<nav class=\"navbar navbar-expand-lg navbar-dark bg-dark fixed-top\">
  <div class=\"container-fluid\">
    <a class=\"navbar-brand\" href=\"/\">Barbie Auto</a>
    <div class=\"collapse navbar-collapse\">
      <ul class=\"navbar-nav me-auto\">
        <li class=\"nav-item\"><a class=\"nav-link\" href=\"/spotify\">Spotify</a></li>
        <li class=\"nav-item\"><a class=\"nav-link\" href=\"/youtube\">YouTube</a></li>
        <li class=\"nav-item\"><a class=\"nav-link\" href=\"/maps\">Waze</a></li>
        <li class=\"nav-item\"><a class=\"nav-link\" href=\"/casino\">Casino</a></li>
      </ul>
    </div>
  </div>
</nav>

<div class=\"container\">
"""

base_footer = """
</div>

<button id=\"mic-btn\" class=\"btn btn-danger rounded-circle shadow\"><b>🎙️</b></button>
<script>
const micBtn = document.getElementById('mic-btn');
micBtn.addEventListener('click', () => {
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'en-US';
    recognition.onresult = function(event) {
        const speech = event.results[0][0].transcript;
        alert('You said: ' + speech);
    };
    recognition.start();
});
</script>
</body>
</html>
"""

@app.route("/")
def home():
    content = """
    <h1 class=\"text-center\">🚗 Welcome to Barbie Auto</h1>
    <p class=\"lead text-center\">Use the navbar to explore Spotify, YouTube, Waze directions, or launch the Barbie Casino.</p>
    """
    return render_template_string(base_header + content + base_footer)

@app.route("/spotify")
def spotify():
    content = """
    <h2>🎧 Spotify Player</h2>
    <p>Say an artist or playlist, then search manually if needed:</p>
    <p><a href=\"https://open.spotify.com\" target=\"_blank\" class=\"btn btn-success\">Open Spotify</a></p>
    <h4 class=\"mt-4\">Featured Playlist</h4>
    <iframe style=\"border-radius:12px\" src=\"https://open.spotify.com/embed/playlist/37i9dQZF1DXcBWIGoYBM5M\"
    width=\"100%\" height=\"600\" frameborder=\"0\" allowfullscreen=\"\"
    allow=\"autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture\"></iframe>
    """
    return render_template_string(base_header + content + base_footer)

@app.route("/youtube")
def youtube():
    query = request.args.get("q", "")
    content = f"""
    <h2>📺 YouTube Search</h2>
    <form method=\"GET\" action=\"/youtube\">
        <input type=\"text\" name=\"q\" class=\"form-control\" placeholder=\"Search YouTube...\" value=\"{query}\">
        <button class=\"btn btn-primary mt-2\">Search</button>
    </form>
    """
    if query:
        content += f"""
        <h4 class=\"mt-4\">Results for '{query}'</h4>
        <iframe width=\"100%\" height=\"500\" src=\"https://www.youtube.com/embed?listType=search&list={query}\" frameborder=\"0\" allowfullscreen></iframe>
        """
    return render_template_string(base_header + content + base_footer)

@app.route("/maps")
def maps():
    content = """
    <h2>🧭 Waze Navigation</h2>
    <p>Embedded Waze map for Rowan University (lat: 39.7092, lon: -75.1209):</p>
    <iframe src=\"https://embed.waze.com/iframe?zoom=14&lat=39.7092&lon=-75.1209\"
    width=\"100%\" height=\"600\" allowfullscreen></iframe>
    """
    return render_template_string(base_header + content + base_footer)

@app.route("/casino")
def casino():
    casino_path = os.path.join(os.path.dirname(__file__), "main.py")
    try:
        subprocess.Popen([sys.executable, casino_path])
        message = "🎰 Barbie Casino launched successfully!"
    except Exception as e:
        message = f"❌ Failed to launch Barbie Casino: {e}"

    content = f"""
    <h2>🎰 Barbie Casino</h2>
    <p>Click the button below to launch the full Tkinter-based Barbie Casino GUI app.</p>
    <div class=\"alert alert-info\">{message}</div>
    """
    return render_template_string(base_header + content + base_footer)

if __name__ == "__main__":
    app.run(debug=True)
