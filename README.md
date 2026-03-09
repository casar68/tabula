# Tabula

Tabula extrait les tableaux contenus dans des fichiers PDF. L'utilisateur uploade un PDF, selectionne visuellement les zones de tableau, et exporte les donnees en CSV, TSV, JSON ou ZIP.

## Stack technique

| Couche | Technologie |
|--------|-------------|
| Backend | Python 3.12, FastAPI, SQLAlchemy, Alembic |
| Base de donnees | PostgreSQL 16 |
| Extraction PDF | PyMuPDF (fitz) + fallback OCR (Tesseract) |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS 4, shadcn/ui |
| Rendu PDF | react-pdf (pdf.js cote client) |
| Etat client | Zustand + TanStack Query |

## Prerequis

- Python 3.12+
- Node.js 22+
- PostgreSQL 16+
- Tesseract OCR (optionnel, pour les PDF a encodage personnalise)

## Installation

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Creer la base de donnees
createdb tabula
alembic upgrade head

# Frontend
cd ../frontend
npm install
```

## Developpement

```bash
# Terminal 1 : backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2 : frontend
cd frontend
npm run dev
```

L'application est accessible sur http://localhost:5173 (le frontend proxy les appels API vers le port 8000).

## Configuration

Copier `.env.example` vers `.env` et ajuster les valeurs :

```bash
cp .env.example .env
```

Variables disponibles :

| Variable | Description | Defaut |
|----------|-------------|--------|
| `DATABASE_URL` | URL de connexion PostgreSQL | `postgresql://postgres:postgres@localhost:5432/tabula` |
| `UPLOAD_DIR` | Repertoire de stockage des PDF | `./uploads` |
| `DEBUG` | Mode debug | `false` |
| `CORS_ORIGINS` | Origines autorisees (JSON) | `["http://localhost:5173"]` |

## Docker

```bash
docker compose up --build
```

L'application est accessible sur http://localhost:8000.

## Tests

```bash
# Backend
cd backend
pytest -v

# Frontend
cd frontend
npm test
```

## Licence

MIT
