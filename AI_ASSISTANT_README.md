# AI Murabbiy Yordamchisi - Qo'llanma

## Tavsif

AI Murabbiy Yordamchisi - bu Google Gemini AI asosida ishlaydigan, tizimdagi real ma'lumotlar (futbolchilar, mashg'ulotlar, o'yinlar, statistikalar) bilan ishlagan holda murabbiyga tavsiyalar beruvchi modul.

## Asosiy Imkoniyatlar

### 1. **Real Ma'lumotlar bilan Ishlash**
AI har bir so'rovda quyidagi ma'lumotlarni tahlil qiladi:
- Jamoa statistikalari (jami futbolchilar, faol o'yinchilar, o'rtacha davomat, reyting)
- O'yinlar statistikasi (g'alabalar, duranglar, mag'lubiyatlar, gollar)
- Mashg'ulotlar statistikasi (davomat, reyting)
- Top futbolchilar (reyting va davomat bo'yicha)
- Muammoli futbolchilar (past davomat, jarohatlar, intizom)

### 2. **Tezkor Hisobotlar**
Bir tugma bosish bilan maxsus tahlillar:
- **Jamoani tahlil qilish** - jamoa holatining umumiy bahosi
- **O'yinchilarni baholash** - har bir futbolchining holati
- **Mashg'ulot rejasi** - keyingi hafta uchun tavsiyalar
- **Kuchli va zaif tomonlar** - jamoaning batafsil tahlili
- **Keyingi o'yin uchun tavsiyalar** - o'yinga tayyorgarlik

### 3. **Chat Interfeysi**
- ChatGPT uslubidagi zamonaviy dizayn
- Real-time javoblar
- Typing indicator (yozayotganini ko'rsatish)
- Auto-scroll
- Xatoliklarni qayta urinish (Retry)
- Dark/Light mode qo'llab-quvvatlash

### 4. **Suhbat Tarixi**
- Barcha suhbatlar bazada saqlanadi
- Har bir murabbiy faqat o'z suhbatlarini ko'radi
- Conversation ID asosida davom ettirish

## O'rnatish

### 1. **Gemini API Key Olish**

1. [Google AI Studio](https://aistudio.google.com/app/apikey) ga kiring
2. "Create API Key" tugmasini bosing
3. API kalitni nusxalang

### 2. **Environment Variable Sozlash**

Backend `.env` faylini yarating (`.env.example` dan nusxa ko'chiring):

```bash
cd backend
copy .env.example .env
```

`.env` faylida `GEMINI_API_KEY` ni o'zgartiring:

```env
GEMINI_API_KEY=sizning-api-kalitingiz-shu-yerga
```

### 3. **Kutubxonalarni O'rnatish**

Gemini kutubxonasi allaqachon `requirements.txt` da bor:

```bash
pip install -r requirements.txt
```

Yoki faqat Gemini:

```bash
pip install google-generativeai>=0.8.3
```

### 4. **Migration Ishga Tushirish**

AI models uchun migratsiya:

```bash
python manage.py migrate
```

Migration fayl allaqachon mavjud: `0019_add_ai_assistant_models.py`

### 5. **Serverni Ishga Tushirish**

```bash
# Backend
python manage.py runserver

# Frontend (boshqa terminal)
cd ../frontend
npm run dev
```

Yoki ikkala serverni bir vaqtda:

```powershell
.\start-dev.ps1
```

## Foydalanish

### Web Interfeys

1. Tizimga kiring
2. Chap menuda **"AI Murabbiy"** tugmasini bosing
3. Tezkor tugmalarni bosing yoki o'z savolingizni yozing

### API Endpointlar

#### 1. **Suhbatlar ro'yxati**
```http
GET /api/ai/conversations/
Authorization: Bearer <access_token>
```

#### 2. **Suhbatni olish**
```http
GET /api/ai/conversations/{id}/
Authorization: Bearer <access_token>
```

#### 3. **Yangi suhbat yaratish**
```http
POST /api/ai/conversations/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "Suhbat nomi"
}
```

#### 4. **Chat (xabar yuborish)**
```http
POST /api/ai/chat/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "message": "Jamoaning holati qanday?",
  "conversation_id": 1  // ixtiyoriy, null bo'lsa yangi yaratadi
}
```

**Javob:**
```json
{
  "success": true,
  "message": "Javob olindi.",
  "data": {
    "conversation_id": 1,
    "user_message": {
      "id": 1,
      "role": "user",
      "content": "Jamoaning holati qanday?",
      "created_at": "2024-01-15T10:30:00Z"
    },
    "ai_message": {
      "id": 2,
      "role": "assistant",
      "content": "Jamoangizning umumiy holati...",
      "created_at": "2024-01-15T10:30:05Z"
    }
  }
}
```

#### 5. **Tezkor hisobot**
```http
POST /api/ai/quick-report/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "report_type": "team_analysis"
}
```

**Report Types:**
- `team_analysis` - Jamoani tahlil qilish
- `player_assessment` - O'yinchilarni baholash
- `training_plan` - Mashg'ulot rejasi
- `strengths_weaknesses` - Kuchli va zaif tomonlar
- `next_match` - Keyingi o'yin tavsiyalari

## Arxitektura

### Backend

**Models** (`core/models.py`):
- `AIConversation` - suhbatlar
- `AIMessage` - xabarlar (user/assistant)

**Views** (`core/api_views.py`):
- `AIConversationViewSet` - CRUD suhbatlar uchun
- `AIChatAPIView` - chat endpoint
- `AIQuickReportAPIView` - tezkor hisobotlar

**Service** (`core/services/gemini_service.py`):
- `GeminiService` - Gemini API integratsiya
- Real ma'lumotlar bilan system prompt yaratish
- Context history bilan ishlash

**Serializers** (`core/api_serializers.py`):
- `AIMessageSerializer`
- `AIConversationSerializer`
- `AIConversationDetailSerializer`
- `AIChatRequestSerializer`

### Frontend

**Page** (`src/app/pages/AIAssistantPage.tsx`):
- React functional component
- Real-time chat UI
- Typing indicator
- Auto-scroll
- Error handling

**API** (`src/app/services/api.ts`):
- `aiAssistantAPI.listConversations()`
- `aiAssistantAPI.getConversation(id)`
- `aiAssistantAPI.createConversation(title)`
- `aiAssistantAPI.chat(message, conversation_id)`
- `aiAssistantAPI.quickReport(report_type)`

**Styles** (`src/app/pages/AIAssistant.css`):
- Responsive dizayn
- Dark/Light mode qo'llab-quvvatlash
- Smooth animatsiyalar

## Xavfsizlik

1. **Authentication** - Faqat login qilgan foydalanuvchilar
2. **Authorization** - Har bir murabbiy faqat o'z suhbatlarini ko'radi
3. **CSRF Protection** - Django CSRF middleware
4. **API Key Security** - Environment variable, kodga yozilmagan
5. **Input Validation** - Serializer level validation

## Troubleshooting

### 1. API Key Error
```
ValueError: GEMINI_API_KEY environment variable kiritilmagan
```
**Yechim:** `.env` faylida `GEMINI_API_KEY` to'g'ri sozlang

### 2. Import Error
```
ModuleNotFoundError: No module named 'google.generativeai'
```
**Yechim:** 
```bash
pip install google-generativeai
```

### 3. Migration Error
```
django.db.utils.OperationalError: no such table: core_aiconversation
```
**Yechim:**
```bash
python manage.py migrate
```

### 4. Frontend Route Not Found
**Yechim:** `App.tsx` da AI Assistant route qo'shilganligini tekshiring

### 5. CORS Error
**Yechim:** `settings.py` da CORS sozlamalari to'g'riligini tekshiring

## Kelajakda Qo'shilishi Mumkin

- [ ] Voice input (ovozli xabar)
- [ ] PDF export (suhbatni PDF qilib yuklab olish)
- [ ] Image analysis (rasm tahlili)
- [ ] Multi-language support (ko'p tillilik)
- [ ] Conversation search (suhbatlarni qidirish)
- [ ] AI training history (AI tarixini ko'rish)
- [ ] Scheduled reports (avtomatik hisobotlar)

## Muallif

Xushnudbek
Futbol Murabbiylari Platformasi
