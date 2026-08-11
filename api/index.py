from app import create_app

app = create_app()

# health check for deployment
@app.route('/_health')
def health():
    return 'ok'