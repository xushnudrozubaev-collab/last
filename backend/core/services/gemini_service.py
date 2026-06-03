"""
Gemini AI Service - Google Gemini API bilan integratsiya
"""
import os
import time
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

try:
    # Yangi versiya (google.genai)
    import google.genai as genai
    USE_NEW_API = True
except ImportError:
    # Eski versiya (google.generativeai)
    import google.generativeai as genai
    USE_NEW_API = False


class GeminiService:
    """Google Gemini AI xizmati"""

    # Afzallikdagi modellar ro'yxati (yuqoridan pastga qarab).
    # Birinchisi ishlamasa, keyingisiga o'tadi.
    # Eslatma: bu modellar shu API key uchun mavjud bo'lishi tekshirilgan.
    # "lite" va "latest" modellar kvota cheklovi yumshoqroq bo'lgani uchun
    # asosiy band modellarga muqobil sifatida ishlatiladi.
    PREFERRED_MODELS = [
        'gemini-2.5-flash',
        'gemini-flash-latest',
        'gemini-2.5-flash-lite',
        'gemini-flash-lite-latest',
        'gemini-2.0-flash-lite',
        'gemini-2.0-flash',
    ]

    # 503 (band) yoki 429 (kvota) xatoliklarda nechta marta qayta urinish
    MAX_RETRIES = 2
    # Qayta urinishlar orasidagi kutish vaqti (soniya)
    RETRY_DELAY = 3

    def __init__(self):
        """Gemini API ni sozlash"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable kiritilmagan")

        self.api_key = api_key
        # Birinchi afzal modelni standart sifatida olamiz.
        self.model_name = self.PREFERRED_MODELS[0]
        self.model = None
        self.client = None

        if USE_NEW_API:
            self.client = genai.Client(api_key=api_key)
        else:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(self.model_name)

        logger.info(f"Gemini Service initialized with model: {self.model_name}")

    def _generate(self, prompt: str, model_name: str) -> str:
        """
        Berilgan model bilan bitta so'rov yuborish.

        Args:
            prompt: To'liq matn (prompt)
            model_name: Ishlatiladigan model nomi

        Returns:
            Model javobi (matn)
        """
        if USE_NEW_API:
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            return response.text
        else:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text

    def _generate_with_fallback(self, prompt: str) -> str:
        """
        Modellar ro'yxati bo'ylab so'rov yuborish.
        Birinchi ishlagani javobni qaytaradi.

        503 (band) va 429 (kvota) xatoliklarida qisqa kutib qayta urinadi.
        404 (mavjud emas) xatoligida darhol keyingi modelga o'tadi.

        Args:
            prompt: To'liq matn (prompt)

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
                    result = self._generate(prompt, model_name)
                    if result:
                        # Ishlagan modelni eslab qolamiz
                        self.model_name = model_name
                        logger.info(f"✅ Javob '{model_name}' modelidan olindi")
                        return result
                except Exception as e:
                    last_error = e
                    error_text = str(e)
                    is_overloaded = '503' in error_text or 'UNAVAILABLE' in error_text
                    is_quota = '429' in error_text or 'RESOURCE_EXHAUSTED' in error_text
                    is_not_found = '404' in error_text or 'NOT_FOUND' in error_text

                    if is_overloaded:
                        had_overload = True
                        logger.warning(
                            f"⏳ '{model_name}' band (503). "
                            f"{self.RETRY_DELAY}s kutib qayta urinaman..."
                        )
                        if attempt < self.MAX_RETRIES:
                            time.sleep(self.RETRY_DELAY)
                            continue
                        # Urinishlar tugadi, keyingi modelga o'tamiz
                        break
                    elif is_quota:
                        had_overload = True
                        logger.warning(
                            f"⚠️ '{model_name}' kvotasi tugagan (429). "
                            f"Keyingi modelga o'taman."
                        )
                        break  # qayta urinish foydasiz, keyingi modelga
                    elif is_not_found:
                        logger.warning(
                            f"❌ '{model_name}' mavjud emas (404). "
                            f"Keyingi modelga o'taman."
                        )
                        break  # keyingi modelga
                    else:
                        logger.warning(f"❌ '{model_name}' xatolik: {error_text}")
                        break  # keyingi modelga

        # Hech qaysi model ishlamadi - foydalanuvchiga tushunarli xabar
        if had_overload:
            raise Exception(
                "Gemini AI hozir juda band yoki kunlik bepul limit tugagan. "
                "Iltimos, bir necha daqiqadan so'ng qayta urinib ko'ring."
            )

        error_text = str(last_error) if last_error else "Noma'lum xatolik"
        logger.error(f"Hech qaysi model ishlamadi. So'nggi xatolik: {error_text}")
        raise Exception(
            "Gemini AI bilan bog'lanishda xatolik yuz berdi. "
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

        # To'liq promptni shakllantirish
        prompt_parts = [system_prompt]

        # Oldingi suhbatlarni qo'shish (oxirgi 10 tasi)
        if conversation_history:
            recent_history = conversation_history[-10:]
            if recent_history:
                prompt_parts.append("\n## OLDINGI SUHBAT\n")
                for msg in recent_history:
                    role = "Murabbiy" if msg["role"] == "user" else "AI Yordamchi"
                    prompt_parts.append(f"{role}: {msg['content']}")

        # Joriy xabarni qo'shish
        prompt_parts.append(f"\n## MURABBIY SAVOLI\n{user_message}")
        prompt_parts.append("\nAniq va amaliy javob bering:")

        full_prompt = "\n".join(prompt_parts)

        return self._generate_with_fallback(full_prompt)

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

- O'zbek tilida javob bering
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
            report_type: Hisobot turi (team_analysis, player_assessment, training_plan, etc.)
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
