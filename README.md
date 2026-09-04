# Gifts Analyzer — цены каждого подарка + графики (Portals + Tonnel)

Без моделей/фонов в v1. Только уровень коллекции. Обновление 3 мин.

## Запуск без docker
```bash
cd backend
pip install -r requirements.txt
python -c "import db; db.init_db()"
uvicorn main:app --port 8000 &
curl -X POST localhost:8000/api/poll   # первый снимок
curl localhost:8000/api/collections | head -c 500
```

```bash
cd frontend
npm install
NEXT_PUBLIC_API=http://localhost:8000 npm run dev
# open http://localhost:3000
```

## Запуск в docker
```bash
docker compose up --build
```

## API
- GET /api/health
- POST /api/poll — дернуть поллер вручную
- GET /api/collections — последний снимок {slug,name,portals_floor,tonnel_floor,spread_pct}
- GET /api/history?slug=plush-pepe&days=7 — история из локальной БД
- GET /api/history-remote?marketplace=portals&scale=day&days=7 — бэкфилл из Giftstat
- GET /api/top?period=24h|7d — топ по % изменения флора

Источник: https://api.giftstat.app (без ключа):
/current/collections, /current/collections/floor, /history/collections/floor, /current/ton-rate
