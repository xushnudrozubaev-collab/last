"""
AI Service - Groq API bilan integratsiya (OpenAI-mos format)

Groq juda tez va bepul limiti katta bo'lgan AI provayder.
API kaliti console.groq.com dan olinadi (gsk_ bilan boshlanadi).
"""
import os
import time
from typing import Dict, List, Optional
import logging

import requests

logger = logging.getLogger(__name__)


class AIService:
    """Groq AI xizmati (OpenAI-mos chat completions API)"""

    # Groq API manzili
    API_URL = "https://api.groq.com/openai/v1/chat/completions"

    # Afzallikdagi modellar ro'yxati (yuqoridan pastga qarab).
    # Birinchisi ishlamasa yoki band bo'lsa, keyingisiga o'tadi.
    PREFERRED_MODELS = [
        "llama-3.3-70b-versatile",   # Eng kuchli, asosiy model
        "openai/gpt-oss-120b",       # Kuchli muqobil
        "llama-3.1-8b-instant",      # Tezkor, yengil zaxira
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "qwen/qwen3-32b",
    ]

    # 503/429 (band/limit) xatoliklarida nechta marta qayta urinish
    MAX_RETRIES = 2
    # Qayta urinishlar orasidagi kutish vaqti (soniya)
    RETRY_DELAY = 3
    # So'rov uchun maksimal kutish vaqti (soniya)
    REQUEST_TIMEOUT = 60

    def __init__(self):
        """AI servisni sozlash"""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable kiritilmagan")

        self.api_key = api_key
        # Birinchi afzal modelni standart sifatida olamiz.
        self.model_name = self.PREFERRED_MODELS[0]

        logger.info(f"AI Service (Groq) initialized with model: {self.model_name}")

    def _request(self, messages: List[Dict[str, str]], model_name: str) -> str:
        """
        Groq API ga bitta so'rov yuborish.

        Args:
            messages: Chat xabarlari ro'yxati (role, content)
            model_name: Ishlatiladigan model nomi

        Returns:
            Model javobi (matn)

        Raises:
            requests.HTTPError: API xatolik qaytarsa
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2048,
        }

        response = requests.post(
            self.API_URL,
            headers=headers,
            json=payload,
            timeout=self.REQUEST_TIMEOUT,
        )

        # Xatolik bo'lsa, status kodni xabarga qo'shamiz
        if response.status_code != 200:
            error_detail = ""
            try:
                error_detail = response.json().get("error", {}).get("message", "")
            except Exception:
                error_detail = response.text[:200]
            raise Exception(f"{response.status_code}: {error_detail}")

        data = response.json()
        return data["choices"][0]["message"]["content"]

    def _generate_with_fallback(self, messages: List[Dict[str, str]]) -> str:
        """
        Modellar ro'yxati bo'ylab so'rov yuborish.
        Birinchi ishlagani javobni qaytaradi.

        503 (band) va 429 (limit) xatoliklarida qisqa kutib qayta urinadi.
        404 (mavjud emas) xatoligida darhol keyingi modelga o'tadi.

        Args:
            messages: Chat xabarlari ro'yxati

        Returns:
            Model javobi (matn)
        """
        last_error: Optional[Exception] = None
        had_overload = False  # 503/429 (vaqtinchalik) xatolik bo'lganmi

        # Avval joriy tanlangan modelni sinaymiz, keyin qolganlarini.
        models_to_try = [self.model_name] + [
            m for m in self.PREFERRED_MODELS if m != self.model_name
        ]

        for model_name in models_to_try:
            for attempt in range(1, self.MAX_RETRIES + 1):
                try:
                    logger.info(
                        f"'{model_name}' modeli bilan so'rov yuborilmoqda "
                        f"(urinish {attempt}/{self.MAX_RETRIES})..."
                    )
                    result = self._request(messages, model_name)
                    if result:
                        # Ishlagan modelni eslab qolamiz
                        self.model_name = model_name
                        logger.info(f"✅ Javob '{model_name}' modelidan olindi")
                        return result
                except Exception as e:
                    last_error = e
                    error_text = str(e)
                    is_overloaded = "503" in error_text or "502" in error_text
                    is_quota = "429" in error_text
                    is_not_found = "404" in error_text or "400" in error_text

                    if is_overloaded:
                        had_overload = True
                        logger.warning(
                            f"⏳ '{model_name}' band (503). "
                            f"{self.RETRY_DELAY}s kutib qayta urinaman..."
                        )
                        if attempt < self.MAX_RETRIES:
                            time.sleep(self.RETRY_DELAY)
                            continue
                        break  # urinishlar tugadi, keyingi modelga
                    elif is_quota:
                        had_overload = True
                        logger.warning(
                            f"⚠️ '{model_name}' limiti tugagan (429). "
                            f"Keyingi modelga o'taman."
                        )
                        break
                    elif is_not_found:
                        logger.warning(
                            f"❌ '{model_name}' mavjud emas yoki noto'g'ri (404/400). "
                            f"Keyingi modelga o'taman."
                        )
                        break
                    else:
                        logger.warning(f"❌ '{model_name}' xatolik: {error_text}")
                        break

        # Hech qaysi model ishlamadi - foydalanuvchiga tushunarli xabar
        if had_overload:
            raise Exception(
                "AI hozir juda band yoki so'rovlar limiti tugagan. "
                "Iltimos, bir necha daqiqadan so'ng qayta urinib ko'ring."
            )

        error_text = str(last_error) if last_error else "Noma'lum xatolik"
        logger.error(f"Hech qaysi model ishlamadi. So'nggi xatolik: {error_text}")
        raise Exception(
            "AI bilan bog'lanishda xatolik yuz berdi. "
            "Iltimos, keyinroq qayta urinib ko'ring."
        )

    def generate_response(
        self,
        user_message: str,
        context_data: Dict,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        AI javob generatsiya qilish

        Args:
            user_message: Foydalanuvchi xabari
            context_data: Tizim statistikalari va ma'lumotlar
            conversation_history: Oldingi suhbat tarixi

        Returns:
            AI yordamchining javobi
        """
        # System prompt - AI rolini belgilash
        system_prompt = self._build_system_prompt(context_data)

        # Chat xabarlarini OpenAI formatida shakllantirish
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt}
        ]

        # Oldingi suhbatlarni qo'shish (oxirgi 10 tasi)
        if conversation_history:
            recent_history = conversation_history[-10:]
            for msg in recent_history:
                role = "assistant" if msg["role"] == "assistant" else "user"
                messages.append({"role": role, "content": msg["content"]})

        # Joriy xabarni qo'shish
        messages.append({"role": "user", "content": user_message})

        return self._generate_with_fallback(messages)

    def _build_system_prompt(self, context_data: Dict) -> str:
        """
        Tizim promptini yaratish - real ma'lumotlar bilan

        Args:
            context_data: Tizimdan olingan statistikalar

        Returns:
            To'liq system prompt
        """
        prompt = """Sen professional futbol murabbiyi va sport analitigisiz. 
Sizning vazifangiz murabbiyga jamoa boshqaruvida yordam berish, tahlil qilish va amaliy tavsiyalar berish.

## TIZIM MA'LUMOTLARI

"""

        # Jamoa statistikalari
        if "team_stats" in context_data:
            stats = context_data["team_stats"]
            prompt += f"""### Jamoa statistikalari:
- Jami futbolchilar: {stats.get('total_players', 0)}
- Faol o'yinchilar: {stats.get('active_players', 0)}
- O'rtacha davomat: {stats.get('attendance_percent', 0)}%
- O'rtacha reyting: {stats.get('average_rating', 0)}

"""

        # O'yinlar statistikasi
        if "matches_stats" in context_data:
            matches = context_data["matches_stats"]
            prompt += f"""### O'yinlar statistikasi:
- Jami o'yinlar: {matches.get('total', 0)}
- G'alabalar: {matches.get('wins', 0)}
- Duranglar: {matches.get('draws', 0)}
- Mag'lubiyatlar: {matches.get('losses', 0)}
- Urilgan gollar: {matches.get('goals_for', 0)}
- O'tkazib yuborilgan gollar: {matches.get('goals_against', 0)}

"""

        # Mashg'ulotlar statistikasi
        if "trainings_stats" in context_data:
            trainings = context_data["trainings_stats"]
            prompt += f"""### Mashg'ulotlar statistikasi:
- Jami mashg'ulotlar: {trainings.get('total', 0)}
- O'rtacha davomat: {trainings.get('average_attendance', 0)}%
- So'nggi haftalik davomat: {trainings.get('recent_attendance', 0)}%

"""

        # Top futbolchilar
        if "top_players" in context_data:
            players = context_data["top_players"]
            if players:
                prompt += "### Eng yaxshi futbolchilar (reyting bo'yicha):\n"
                for i, player in enumerate(players[:5], 1):
                    prompt += f"{i}. {player['name']} - {player['rating']} reyting, {player['attendance']}% davomat\n"
                prompt += "\n"

        # Muammoli futbolchilar
        if "problem_players" in context_data:
            problems = context_data["problem_players"]
            if problems:
                prompt += "### Diqqat talab qiladigan futbolchilar:\n"
                for player in problems[:3]:
                    prompt += f"- {player['name']}: {player['issue']}\n"
                prompt += "\n"

        # Jarohatli futbolchilar
        if "injured_players" in context_data:
            injured = context_data["injured_players"]
            if injured:
                prompt += f"### Jarohatli futbolchilar: {len(injured)} kishi\n\n"

        prompt += """
## SIZNING VAZIFALARINGIZ

1. **Tahlil qilish**: Yuqoridagi ma'lumotlar asosida jamoa holatini baholash
2. **Tavsiyalar berish**: Aniq va amaliy maslahatlar berish
3. **Muammolarni aniqlash**: Zaif tomonlar va yechimlarni ko'rsatish
4. **Rejalashtirish**: Mashg'ulot va o'yin rejalari tuzishda yordam

## JAVOB BERISH QOIDALARI

- Faqat o'zbek tilida javob bering
- Qisqa va aniq javoblar bering
- Raqamlar va faktlar bilan asoslang
- Amaliy tavsiyalar bering
- Professional va do'stona ohangda gapiring
- Agar ma'lumot yetarli bo'lmasa, buni aytib o'ting

Murabbiy savoliga aniq va foydali javob bering."""

        return prompt

    def generate_quick_report(self, report_type: str, context_data: Dict) -> str:
        """
        Tezkor hisobot generatsiya qilish

        Args:
            report_type: Hisobot turi (team_analysis, player_assessment, etc.)
            context_data: Tizim ma'lumotlari

        Returns:
            Generatsiya qilingan hisobot
        """
        prompts = {
            "team_analysis": "Jamoaning umumiy holatini tahlil qiling. Kuchli va zaif tomonlarni ko'rsating.",
            "player_assessment": "O'yinchilar holatini baholang. Kim yaxshi ishlayapti, kimga ko'proq e'tibor kerak?",
            "training_plan": "Keyingi haftaga mashg'ulot rejasi taklif qiling. Nimaga e'tibor berish kerak?",
            "strengths_weaknesses": "Jamoaning kuchli va zaif tomonlarini batafsil tahlil qiling.",
            "next_match": "Keyingi o'yinga tayyorgarlik uchun tavsiyalar bering. Nimaga e'tibor qaratish kerak?"
        }

        user_message = prompts.get(report_type, "Jamoa haqida umumiy ma'lumot bering.")

        return self.generate_response(
            user_message=user_message,
            context_data=context_data,
            conversation_history=None
        )
