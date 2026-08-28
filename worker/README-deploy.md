# TV FREEDOM Cloud (Cloudflare Workers CDN)

Serves the GitHub playlists over **HTTPS** with a clean URL, caching + CORS,
from any free Cloudflare Workers account. No OAuth token, no wrangler on this
box — the GitHub Actions workflow deploys it for you.

## One-time setup (from any healthy machine, ~3 min)
1. Cloudflare dashboard → Workers & Pages → create `tv-matrix` (free plan, `workers.dev` subdomain).
2. Dashboard → My Profile → API Tokens → Create Token → template
   **"Edit Cloudflare Workers"** → note the token.
3. In repo `didicola/tv-matrix` → Settings → Secrets and variables → Actions, add:
   - `CF_API_TOKEN` = the token
   - `CF_ACCOUNT_ID` = your account id (dashboard home page left)
4. Push this folder into the repo (`worker/` + `.github/workflows/deploy-cf.yml`) — done automatically next time you push.

## Result
- `https://tv-matrix.<account>.workers.dev/mega.m3u` (3238 chaînes)
- `https://tv-matrix.<account>.workers.dev/eu.m3u`
- `https://tv-matrix.<account>.workers.dev/films.m3u`
- `https://tv-matrix.<account>.workers.dev/` portal (FR + AR)

On the TV app: menu → "Changer la liste TV" → paste that URL. The GitHub raw
URLs keep working as fallback.