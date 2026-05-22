# Football Coach Platform

Bu loyiha ikki qismdan iborat bitta platforma:

- `backend/` - Django backend va REST API
- `frontend/` - React + Vite frontend

Asosiy ishlatiladigan sayt:

```text
http://127.0.0.1:5173
```

Backend API alohida ishlaydi:

```text
http://127.0.0.1:8000/api
```

## Bitta Buyruq Bilan Ishga Tushirish

Windows PowerShell terminalida loyiha rootida bajaring:

```powershell
.\start-dev.ps1
```

Script quyidagilarni qiladi:

- backend `.venv` bo'lmasa yaratadi
- Python kutubxonalarini o'rnatadi
- frontend `node_modules` bo'lmasa `npm install` qiladi
- Django migrationlarni bajaradi
- backendni `127.0.0.1:8000` da ishga tushiradi
- frontendni `127.0.0.1:5173` da ishga tushiradi

## Muhim

`127.0.0.1:8000` Django API va admin uchun.

`127.0.0.1:5173` yangi asosiy React sayt.

Frontend API manzili default:

```text
http://127.0.0.1:8000/api
```

Production deployda `VITE_API_URL` alohida berilishi kerak.
