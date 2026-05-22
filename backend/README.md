# Coach Platform Backend

Django backend faqat REST API va Django admin uchun ishlatiladi.

Asosiy frontend `../frontend` papkasida.

## Local

Root papkadan bitta buyruq ishlating:

```powershell
.\start-dev.ps1
```

Backend alohida kerak bo'lsa:

```powershell
cd backend
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

API:

```text
http://127.0.0.1:8000/api
```

Admin:

```text
http://127.0.0.1:8000/admin
```
