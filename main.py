from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
import os
import uvicorn
from dotenv import load_dotenv

load_dotenv()  
app = FastAPI(title="Fitty Backend")

# Aggiungi il middleware delle sessioni (fondamentale per oauth)
app.add_middleware(SessionMiddleware, secret_key=os.urandom(24)) # Usa una chiave sicura e fissa in produzione!
CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")
CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET")
USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
# Inizializza OAuth
oauth = OAuth()
 
oauth.register(
    name='oidc',
    server_metadata_url=f'https://cognito-idp.eu-west-3.amazonaws.com/{USER_POOL_ID}/.well-known/openid-configuration',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    client_kwargs={'scope': 'email openid profile'}
)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    user = request.session.get('user')
    if user:
        return f'Hello, {user.get("email")}. <br><a href="/logout">Logout</a>'
    else:
        return 'Welcome! Please <a href="/login">Login</a>.'

@app.get("/login")
async def login(request: Request):
    # Opzione 1: Puoi reindirizzare all'endpoint del backend (come nel tuo esempio Flask)
    redirect_uri = str(request.url_for('authorize'))
    
    # Opzione 2: Desideri ritornare alla pagina callback del client web (NextJS o simile)
    # redirect_uri = 'http://localhost:3000/api/auth/callback/cognito'

    return await oauth.oidc.authorize_redirect(request, redirect_uri)

@app.get("/authorize")
async def authorize(request: Request):
    # Ottiene il token access
    token = await oauth.oidc.authorize_access_token(request)
    # Ricava l'user info
    user = token.get('userinfo')
    
    if user:
        request.session['user'] = user
        
    return RedirectResponse(url='/')

@app.get("/logout")
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url='/')


if __name__ == '__main__':
    # Avvia con l'auto-reload
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
