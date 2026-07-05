# PawMatch

Separate Django pet adoption project with **Haversine** proximity search and **cosine similarity** recommendations.

## Project structure

```
pawmatch/
├── manage.py
├── requirements.txt
├── pawmatch/              # Django project settings
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   └── adoption/          # Pet adoption app
│       ├── models.py
│       ├── views.py
│       ├── urls.py
│       ├── forms.py
│       ├── utils.py       # Haversine + cosine algorithms
│       ├── admin.py
│       ├── templates/adoption/
│       └── management/commands/seed_pets.py
├── static/css/main.css
├── media/
└── db.sqlite3
```

## Setup

```bash
cd pawmatch
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_pets
python manage.py runserver
```

Open http://127.0.0.1:8000/

## Demo accounts

| Role    | Username      | Password     |
|---------|---------------|--------------|
| Shelter | shelteradmin  | admin12345   |
| Adopter | adopter1      | adopter123   |

## Features

- **Haversine** — find pets/shelters sorted by distance from your location
- **Cosine similarity** — personalized pet recommendations from adoption history
- **Khalti payment** — same ePayment + checkout widget integration as `ca/` car rental
- Adoption application workflow (apply → shelter review → pay via Khalti)
- Shelter admin dashboard for managing pets and applications
- Warm, mobile-friendly UI

## Payment (Khalti)

| URL | Purpose |
|-----|---------|
| `/init-khalti/` | Start Khalti ePayment |
| `/verify-khalti/` | Khalti return/callback |
| `/verify-payment/` | Khalti checkout widget verification |
| `/applications/confirmation/<id>/` | Payment page with Khalti button |

## Note

This is a **separate project** from the car rental app in `ca/`. The car rental codebase is unchanged.
