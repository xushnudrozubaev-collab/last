# Coach Platform

Futbol murabbiylari uchun raqamli kundalik va statistika platformasi.

## Ishga tushirish

1. `python -m venv .venv`
2. `.venv\Scripts\activate`
3. `pip install -r requirements.txt`
4. `.env.example` asosida `.env` yarating
5. `python manage.py migrate`
6. `python manage.py loaddata fixtures/sample_data.json`
7. `python manage.py createsuperuser`
8. `python manage.py runserver`

## Asosiy yo'nalish

- Figma export'dagi sidebar, navbar, kartalar va oq-ko'k premium sport uslubi saqlandi
- Frontend `Django Templates + HTML + CSS + JavaScript` bilan yozildi
- PostgreSQL env orqali yoqiladi, kerak bo'lsa lokal test uchun SQLite fallback ham mavjud
