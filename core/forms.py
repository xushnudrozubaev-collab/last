from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.forms import AuthenticationForm

from .models import Match, Player, Training, UserProfile


class StyledFormMixin:
    input_class = "form-control"

    def apply_styles(self):
        for name, field in self.fields.items():
            css_class = field.widget.attrs.get("class", "")
            extra_classes = [self.input_class]
            input_type = getattr(field.widget, "input_type", "")

            if isinstance(field.widget, forms.Select):
                extra_classes.append("form-select-control")
            elif isinstance(field.widget, forms.Textarea):
                extra_classes.append("form-textarea-control")
            elif isinstance(field.widget, forms.ClearableFileInput):
                extra_classes.append("form-file-control")
            elif input_type == "date":
                extra_classes.append("form-date-control")
            elif input_type == "time":
                extra_classes.append("form-time-control")
            elif input_type == "number":
                extra_classes.append("form-number-control")

            field.widget.attrs["class"] = f"{css_class} {' '.join(extra_classes)}".strip()
            field.widget.attrs.setdefault("data-field-name", name)

            if not isinstance(field.widget, (forms.Select, forms.ClearableFileInput)):
                field.widget.attrs.setdefault("placeholder", field.label)

            if input_type in {"date", "time"}:
                field.widget.attrs["placeholder"] = ""

            field.error_messages.setdefault("required", "Bu maydonni to'ldirish majburiy.")
            field.error_messages.setdefault("invalid", "Kiritilgan qiymat noto'g'ri.")

    def localize_common_errors(self):
        for field in self.fields.values():
            if isinstance(field, forms.EmailField):
                field.error_messages["invalid"] = "To'g'ri elektron pochta manzilini kiriting."
            if isinstance(field, forms.DecimalField):
                field.error_messages.setdefault("invalid", "To'g'ri son kiriting.")
            if isinstance(field, forms.IntegerField):
                field.error_messages.setdefault("invalid", "Butun son kiriting.")
            if hasattr(field, "min_value") and field.min_value is not None:
                field.error_messages.setdefault("min_value", f"Qiymat kamida {field.min_value} bo'lishi kerak.")
            if hasattr(field, "max_value") and field.max_value is not None:
                field.error_messages.setdefault("max_value", f"Qiymat {field.max_value} dan oshmasligi kerak.")


class LoginForm(AuthenticationForm, StyledFormMixin):
    username = forms.CharField(widget=forms.TextInput(attrs={"placeholder": "username@example.com"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder": "••••••••"}))
    error_messages = {
        "invalid_login": "Foydalanuvchi nomi yoki parol noto'g'ri. Iltimos, qayta urinib ko'ring.",
        "inactive": "Bu hisob hozir faol emas.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()
        self.localize_common_errors()
        self.fields["username"].label = "Foydalanuvchi nomi"
        self.fields["username"].widget.attrs["placeholder"] = "Foydalanuvchi nomingizni kiriting"
        self.fields["password"].label = "Parol"
        self.fields["password"].widget.attrs["placeholder"] = "Parolingizni kiriting"


class UserSettingsForm(forms.ModelForm, StyledFormMixin):
    full_name = forms.CharField(max_length=150, label="To'liq ism")
    email = forms.EmailField(label="Elektron pochta")
    role = forms.CharField(label="Lavozim", required=False)

    class Meta:
        model = UserProfile
        fields = [
            "phone",
            "avatar",
            "language",
            "theme",
            "email_notifications",
            "sms_notifications",
            "system_alerts",
        ]
        labels = {
            "phone": "Telefon",
            "avatar": "Avatar",
            "language": "Til",
            "theme": "Mavzu",
            "email_notifications": "Elektron pochta bildirishnomasi",
            "sms_notifications": "SMS bildirishnoma",
            "system_alerts": "Tizim ogohlantirishlari",
        }

    def __init__(self, *args, user=None, coach_profile=None, **kwargs):
        self.user = user
        self.coach_profile = coach_profile
        super().__init__(*args, **kwargs)
        self.fields["full_name"].initial = user.get_full_name() or user.username
        self.fields["email"].initial = user.email
        self.fields["role"].initial = coach_profile.role if coach_profile else "Murabbiy"
        self.fields["role"].widget.attrs.update({"readonly": "readonly"})
        self.apply_styles()
        self.localize_common_errors()
        for checkbox_name in ("email_notifications", "sms_notifications", "system_alerts"):
            self.fields[checkbox_name].widget.attrs["class"] = "switch-input"
        self.fields["full_name"].widget.attrs["placeholder"] = "To'liq ism-familiya"
        self.fields["email"].widget.attrs["placeholder"] = "Elektron pochta manzili"
        self.fields["phone"].widget.attrs["placeholder"] = "Telefon raqami"
        self.fields["role"].widget.attrs["placeholder"] = "Lavozim"

    def save(self, commit=True):
        profile = super().save(commit=False)
        full_name = self.cleaned_data["full_name"].strip()
        name_parts = full_name.split(maxsplit=1)
        self.user.first_name = name_parts[0] if name_parts else ""
        self.user.last_name = name_parts[1] if len(name_parts) > 1 else ""
        self.user.email = self.cleaned_data["email"]
        if commit:
            self.user.save()
            profile.save()
        return profile


class StyledPasswordChangeForm(PasswordChangeForm, StyledFormMixin):
    old_password = forms.CharField(label="Eski parol", widget=forms.PasswordInput(attrs={"placeholder": "Eski parol"}))
    new_password1 = forms.CharField(
        label="Yangi parol",
        widget=forms.PasswordInput(attrs={"placeholder": "Yangi parol"}),
        help_text="Parol kamida 8 ta belgidan iborat bo'lsin, juda oddiy yoki faqat raqamlardan iborat bo'lmasin.",
    )
    new_password2 = forms.CharField(label="Parolni tasdiqlash", widget=forms.PasswordInput(attrs={"placeholder": "Parolni tasdiqlash"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()
        self.localize_common_errors()
        self.error_messages["password_incorrect"] = "Eski parol noto'g'ri kiritildi."
        self.error_messages["password_mismatch"] = "Yangi parollar bir-biriga mos kelmadi."


class PlayerForm(forms.ModelForm, StyledFormMixin):
    join_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))

    class Meta:
        model = Player
        fields = [
            "full_name",
            "shirt_number",
            "position",
            "age",
            "nationality",
            "height",
            "weight",
            "join_date",
            "short_note",
            "photo",
        ]
        labels = {
            "full_name": "To'liq ism",
            "shirt_number": "Futbolka raqami",
            "position": "Pozitsiya",
            "age": "Yosh",
            "nationality": "Millati",
            "height": "Bo'yi",
            "weight": "Vazni",
            "join_date": "Qo'shilgan sana",
            "short_note": "Qisqacha izoh",
            "photo": "Rasm",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()
        self.localize_common_errors()
        self.fields["full_name"].widget.attrs["placeholder"] = "Futbolchi ism-familiyasi"
        self.fields["shirt_number"].widget.attrs["placeholder"] = "Masalan, 10"
        self.fields["age"].widget.attrs["placeholder"] = "Yosh"
        self.fields["nationality"].widget.attrs["placeholder"] = "Millati"
        self.fields["height"].widget.attrs["placeholder"] = "Masalan, 1.78"
        self.fields["weight"].widget.attrs["placeholder"] = "Masalan, 76"
        self.fields["short_note"].widget.attrs["placeholder"] = "Futbolchi haqida qisqa izoh"
        self.fields["photo"].widget.attrs["accept"] = "image/*"


class MatchForm(forms.ModelForm, StyledFormMixin):
    match_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    match_time = forms.TimeField(widget=forms.TimeInput(attrs={"type": "time"}))

    class Meta:
        model = Match
        fields = [
            "home_team",
            "away_team",
            "home_logo_url",
            "away_logo_url",
            "match_date",
            "match_time",
            "stadium",
            "status",
            "home_score",
            "away_score",
            "attendance",
            "referee",
            "note",
        ]
        labels = {
            "home_team": "Uy jamoasi",
            "away_team": "Mehmon jamoa",
            "home_logo_url": "Uy jamoasi logosi",
            "away_logo_url": "Mehmon jamoa logosi",
            "match_date": "O'yin sanasi",
            "match_time": "Boshlanish vaqti",
            "stadium": "Stadion",
            "status": "Holat",
            "home_score": "Uy jamoasi gollari",
            "away_score": "Mehmon jamoa gollari",
            "attendance": "Tomoshabinlar soni",
            "referee": "Hakam",
            "note": "Izoh",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()
        self.localize_common_errors()
        self.fields["home_team"].widget.attrs["placeholder"] = "Uy jamoasi nomi"
        self.fields["away_team"].widget.attrs["placeholder"] = "Mehmon jamoa nomi"
        self.fields["home_logo_url"].widget.attrs["placeholder"] = "Logo havolasi"
        self.fields["away_logo_url"].widget.attrs["placeholder"] = "Logo havolasi"
        self.fields["stadium"].widget.attrs["placeholder"] = "Stadion nomi"
        self.fields["attendance"].widget.attrs["placeholder"] = "Tomoshabinlar soni"
        self.fields["referee"].widget.attrs["placeholder"] = "Hakam ismi"
        self.fields["note"].widget.attrs["placeholder"] = "O'yin haqida qisqacha izoh"


class TrainingForm(forms.ModelForm, StyledFormMixin):
    training_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    start_time = forms.TimeField(widget=forms.TimeInput(attrs={"type": "time"}))
    end_time = forms.TimeField(widget=forms.TimeInput(attrs={"type": "time"}))

    class Meta:
        model = Training
        fields = [
            "title",
            "training_type",
            "training_date",
            "start_time",
            "end_time",
            "location",
            "attendance_total",
            "attendance_present",
            "note",
        ]
        labels = {
            "title": "Mashg'ulot nomi",
            "training_type": "Mashg'ulot turi",
            "training_date": "Mashg'ulot sanasi",
            "start_time": "Boshlanish vaqti",
            "end_time": "Tugash vaqti",
            "location": "Joylashuv",
            "attendance_total": "Jami qatnashuvchilar",
            "attendance_present": "Kelganlar soni",
            "note": "Izoh",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()
        self.localize_common_errors()
        self.fields["title"].widget.attrs["placeholder"] = "Mashg'ulot nomi"
        self.fields["location"].widget.attrs["placeholder"] = "Mashg'ulot joyi"
        self.fields["attendance_total"].widget.attrs["placeholder"] = "Jami qatnashuvchilar"
        self.fields["attendance_present"].widget.attrs["placeholder"] = "Kelganlar soni"
        self.fields["note"].widget.attrs["placeholder"] = "Mashg'ulot haqida izoh"

