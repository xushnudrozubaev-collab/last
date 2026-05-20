from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from urllib.parse import quote


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CoachProfile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="coach_profile")
    full_name = models.CharField(max_length=150)
    role = models.CharField(max_length=100, default="Bosh murabbiy")
    phone = models.CharField(max_length=30, blank=True)
    club_name = models.CharField(max_length=150, default="CoachPro Academy")
    experience_years = models.PositiveIntegerField(default=5)
    bio = models.TextField(blank=True)

    class Meta:
        verbose_name = "murabbiy profili"
        verbose_name_plural = "murabbiy profillari"

    def __str__(self):
        return self.full_name


class UserProfile(TimeStampedModel):
    LANGUAGE_UZ = "uz"
    LANGUAGE_RU = "ru"
    LANGUAGE_EN = "en"
    LANGUAGE_CHOICES = [
        (LANGUAGE_UZ, "O'zbek"),
        (LANGUAGE_RU, "Ruscha"),
        (LANGUAGE_EN, "Inglizcha"),
    ]

    THEME_LIGHT = "light"
    THEME_DARK = "dark"
    THEME_CHOICES = [
        (THEME_LIGHT, "Yorug'"),
        (THEME_DARK, "Qorong'i"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="user_profile")
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default=LANGUAGE_UZ)
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default=THEME_LIGHT)
    phone = models.CharField(max_length=30, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    system_alerts = models.BooleanField(default=True)

    class Meta:
        verbose_name = "foydalanuvchi profili"
        verbose_name_plural = "foydalanuvchi profillari"

    def __str__(self):
        return f"{self.user.username} profili"


class Player(TimeStampedModel):
    POSITION_FORWARD = "forward"
    POSITION_MIDFIELDER = "midfielder"
    POSITION_DEFENDER = "defender"
    POSITION_GOALKEEPER = "goalkeeper"
    POSITION_CHOICES = [
        (POSITION_FORWARD, "Hujumchi"),
        (POSITION_MIDFIELDER, "Yarim himoyachi"),
        (POSITION_DEFENDER, "Himoyachi"),
        (POSITION_GOALKEEPER, "Darvozabon"),
    ]

    full_name = models.CharField(max_length=150)
    shirt_number = models.PositiveIntegerField(default=1)
    position = models.CharField(max_length=20, choices=POSITION_CHOICES)
    age = models.PositiveIntegerField()
    nationality = models.CharField(max_length=80)
    height = models.DecimalField(max_digits=4, decimal_places=2, help_text="Metrlarda")
    weight = models.PositiveIntegerField(help_text="Kilogramm")
    join_date = models.DateField()
    photo = models.ImageField(upload_to="players/", blank=True, null=True)
    short_note = models.CharField(max_length=180, blank=True)

    class Meta:
        ordering = ["shirt_number", "full_name"]
        verbose_name = "futbolchi"
        verbose_name_plural = "futbolchilar"

    def __str__(self):
        return self.full_name

    def get_absolute_url(self):
        return reverse("player_detail", args=[self.pk])

    @property
    def initials(self):
        parts = [part[0] for part in self.full_name.split()[:2] if part]
        return "".join(parts).upper() or "PL"

    @property
    def avatar_url(self):
        initials = self.initials
        svg = f"""
        <svg xmlns='http://www.w3.org/2000/svg' width='256' height='256' viewBox='0 0 256 256'>
          <defs>
            <linearGradient id='g' x1='0%' y1='0%' x2='100%' y2='100%'>
              <stop offset='0%' stop-color='#1d8fc7'/>
              <stop offset='100%' stop-color='#0ea5d9'/>
            </linearGradient>
          </defs>
          <circle cx='128' cy='128' r='128' fill='url(#g)' />
          <text x='50%' y='52%' dominant-baseline='middle' text-anchor='middle'
                font-family='Inter, Arial, sans-serif' font-size='92' font-weight='700' fill='#ffffff'>
            {initials}
          </text>
        </svg>
        """.strip()
        return f"data:image/svg+xml;utf8,{quote(svg)}"

    @property
    def photo_display_url(self):
        if not self.photo:
            return ""
        try:
            modified = self.photo.storage.get_modified_time(self.photo.name)
            version = int(modified.timestamp())
        except Exception:
            version = int(self.updated_at.timestamp()) if self.updated_at else 0
        return f"{self.photo.url}?v={version}"


class Match(TimeStampedModel):
    STATUS_UPCOMING = "upcoming"
    STATUS_LIVE = "live"
    STATUS_PLAYED = "played"
    STATUS_CHOICES = [
        (STATUS_UPCOMING, "Kelgusi"),
        (STATUS_LIVE, "Jonli"),
        (STATUS_PLAYED, "Tugagan"),
    ]

    home_team = models.CharField(max_length=150)
    away_team = models.CharField(max_length=150)
    home_logo_url = models.URLField(blank=True)
    away_logo_url = models.URLField(blank=True)
    match_date = models.DateField()
    match_time = models.TimeField()
    stadium = models.CharField(max_length=150)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_UPCOMING)
    home_score = models.PositiveIntegerField(blank=True, null=True)
    away_score = models.PositiveIntegerField(blank=True, null=True)
    attendance = models.PositiveIntegerField(blank=True, null=True)
    referee = models.CharField(max_length=120, blank=True)
    possession_percent = models.PositiveSmallIntegerField(
        default=50,
        validators=[
            MinValueValidator(0, message="To'p nazorati 0 dan kam bo'lishi mumkin emas."),
            MaxValueValidator(100, message="To'p nazorati 100 dan oshmasligi kerak."),
        ],
    )
    shots = models.PositiveIntegerField(default=0)
    shots_on_target = models.PositiveIntegerField(default=0)
    corners = models.PositiveIntegerField(default=0)
    yellow_cards = models.PositiveIntegerField(default=0)
    red_cards = models.PositiveIntegerField(default=0)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["-match_date", "-match_time"]
        verbose_name = "o'yin"
        verbose_name_plural = "o'yinlar"

    def __str__(self):
        return f"{self.home_team} vs {self.away_team}"

    def get_absolute_url(self):
        return reverse("match_detail", args=[self.pk])

    @property
    def result_label(self):
        if self.home_score is None or self.away_score is None:
            return "Rejalashtirilgan"
        if self.home_score > self.away_score:
            return "G'alaba"
        if self.home_score < self.away_score:
            return "Mag'lubiyat"
        return "Durang"


class Training(TimeStampedModel):
    TYPE_TACTICS = "tactics"
    TYPE_FITNESS = "fitness"
    TYPE_RECOVERY = "recovery"
    TYPE_TECHNICAL = "technical"
    TYPE_CHOICES = [
        (TYPE_TACTICS, "Taktika"),
        (TYPE_FITNESS, "Jismoniy"),
        (TYPE_RECOVERY, "Tiklanish"),
        (TYPE_TECHNICAL, "Texnik"),
    ]

    title = models.CharField(max_length=150)
    training_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    training_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=150)
    note = models.TextField(blank=True)
    attendance_total = models.PositiveIntegerField(default=0)
    attendance_present = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["training_date", "start_time"]
        verbose_name = "mashg'ulot"
        verbose_name_plural = "mashg'ulotlar"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("training_list")

    @property
    def duration_display(self):
        start_minutes = self.start_time.hour * 60 + self.start_time.minute
        end_minutes = self.end_time.hour * 60 + self.end_time.minute
        duration = max(end_minutes - start_minutes, 0)
        hours = duration // 60
        minutes = duration % 60
        if hours and minutes:
            return f"{hours} soat {minutes} daqiqa"
        if hours:
            return f"{hours} soat"
        return f"{minutes} daqiqa"

    @property
    def attendance_percent(self):
        if not self.attendance_total:
            return 0
        return round((self.attendance_present / self.attendance_total) * 100)

    @property
    def attendance_display(self):
        return f"{self.attendance_present}/{self.attendance_total}"


class TrainingAttendance(TimeStampedModel):
    STATUS_PRESENT = "Qatnashdi"
    STATUS_ABSENT = "Qatnashmadi"
    STATUS_LATE = "Kechikdi"
    STATUS_EXCUSED = "Uzrli sabab"
    STATUS_CHOICES = [
        (STATUS_PRESENT, "Qatnashdi"),
        (STATUS_ABSENT, "Qatnashmadi"),
    ]

    INJURY_NO = "Yo'q"
    INJURY_YES = "Bor"
    INJURY_RECOVERING = "Tiklanmoqda"
    INJURY_CHOICES = [
        (INJURY_NO, "Yo'q"),
        (INJURY_YES, "Bor"),
        (INJURY_RECOVERING, "Tiklanmoqda"),
    ]

    PHYSICAL_EXCELLENT = "excellent"
    PHYSICAL_GOOD = "good"
    PHYSICAL_AVERAGE = "average"
    PHYSICAL_TIRED = "tired"
    PHYSICAL_INJURED = "injured"
    PHYSICAL_CHOICES = [
        (PHYSICAL_EXCELLENT, "Zo'r"),
        (PHYSICAL_GOOD, "Yaxshi"),
        (PHYSICAL_AVERAGE, "O'rtacha"),
        (PHYSICAL_TIRED, "Charchagan"),
        (PHYSICAL_INJURED, "Jarohatlangan"),
    ]

    ACTIVITY_LOW = "low"
    ACTIVITY_MEDIUM = "medium"
    ACTIVITY_HIGH = "high"
    ACTIVITY_CHOICES = [
        (ACTIVITY_LOW, "Past"),
        (ACTIVITY_MEDIUM, "O'rtacha"),
        (ACTIVITY_HIGH, "Yuqori"),
    ]

    DISCIPLINE_GOOD = "good"
    DISCIPLINE_WARNING = "warning"
    DISCIPLINE_PROBLEM = "problem"
    DISCIPLINE_CHOICES = [
        (DISCIPLINE_GOOD, "Yaxshi"),
        (DISCIPLINE_WARNING, "Ogohlantirish"),
        (DISCIPLINE_PROBLEM, "Muammo bor"),
    ]

    training = models.ForeignKey(Training, on_delete=models.CASCADE, related_name="attendance_records")
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="training_attendance_records")
    attendance_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PRESENT)
    physical_condition = models.CharField(
        max_length=20,
        choices=PHYSICAL_CHOICES,
        default=PHYSICAL_GOOD,
    )
    activity_level = models.CharField(
        max_length=20,
        choices=ACTIVITY_CHOICES,
        default=ACTIVITY_MEDIUM,
    )
    discipline = models.CharField(
        max_length=20,
        choices=DISCIPLINE_CHOICES,
        default=DISCIPLINE_GOOD,
    )
    rating = models.PositiveSmallIntegerField(
        default=7,
        validators=[
            MinValueValidator(1, message="Baho 1 dan 10 gacha bo'lishi kerak."),
            MaxValueValidator(10, message="Baho 1 dan 10 gacha bo'lishi kerak."),
        ],
    )
    attended_minutes = models.PositiveIntegerField(
        default=90,
        validators=[MinValueValidator(0, message="Qatnashgan daqiqa manfiy bo'lishi mumkin emas.")],
    )
    training_duration_minutes = models.PositiveIntegerField(
        default=90,
        validators=[MinValueValidator(1, message="Mashg'ulot davomiyligi 1 daqiqadan kam bo'lmasligi kerak.")],
    )
    fatigue_level = models.PositiveSmallIntegerField(
        default=1,
        validators=[
            MinValueValidator(1, message="Charchoq darajasi 1 dan 10 gacha bo'lishi kerak."),
            MaxValueValidator(10, message="Charchoq darajasi 1 dan 10 gacha bo'lishi kerak."),
        ],
    )
    pain_level = models.PositiveSmallIntegerField(
        default=1,
        validators=[
            MinValueValidator(1, message="Og'riq darajasi 1 dan 10 gacha bo'lishi kerak."),
            MaxValueValidator(10, message="Og'riq darajasi 1 dan 10 gacha bo'lishi kerak."),
        ],
    )
    sleep_quality = models.PositiveSmallIntegerField(
        default=7,
        validators=[
            MinValueValidator(1, message="Uyqu sifati 1 dan 10 gacha bo'lishi kerak."),
            MaxValueValidator(10, message="Uyqu sifati 1 dan 10 gacha bo'lishi kerak."),
        ],
    )
    activity_score = models.PositiveSmallIntegerField(
        default=7,
        validators=[
            MinValueValidator(1, message="Faollik bahosi 1 dan 10 gacha bo'lishi kerak."),
            MaxValueValidator(10, message="Faollik bahosi 1 dan 10 gacha bo'lishi kerak."),
        ],
    )
    heart_rate = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=[
            MinValueValidator(30, message="Yurak urishi kamida 30 bpm bo'lishi kerak."),
            MaxValueValidator(240, message="Yurak urishi 240 bpm dan oshmasligi kerak."),
        ],
    )
    blood_pressure = models.CharField(max_length=20, blank=True)
    body_temperature = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    measured_weight = models.DecimalField(max_digits=5, decimal_places=1, blank=True, null=True)
    measured_height = models.PositiveSmallIntegerField(blank=True, null=True)
    oxygen_saturation = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=[
            MinValueValidator(50, message="Kislorod darajasi kamida 50% bo'lishi kerak."),
            MaxValueValidator(100, message="Kislorod darajasi 100% dan oshmasligi kerak."),
        ],
    )
    respiratory_rate = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=[
            MinValueValidator(5, message="Nafas olish tezligi kamida 5 marta/min bo'lishi kerak."),
            MaxValueValidator(80, message="Nafas olish tezligi 80 marta/min dan oshmasligi kerak."),
        ],
    )
    injury_status = models.CharField(max_length=20, choices=INJURY_CHOICES, default=INJURY_NO)
    injury_note = models.CharField(max_length=180, blank=True)
    coach_note = models.TextField(blank=True)

    class Meta:
        ordering = ["-training__training_date", "player__shirt_number", "player__full_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["training", "player"],
                name="unique_training_player_attendance",
            )
        ]
        verbose_name = "mashg'ulot davomadi"
        verbose_name_plural = "mashg'ulot davomadi"

    def __str__(self):
        return f"{self.training} - {self.player} - {self.attendance_status}"

    def clean(self):
        errors = {}
        if self.attended_minutes < 0:
            errors["attended_minutes"] = "Qatnashgan daqiqa manfiy bo'lishi mumkin emas."
        if self.training_duration_minutes <= 0:
            errors["training_duration_minutes"] = "Mashg'ulot davomiyligi 1 daqiqadan kam bo'lmasligi kerak."
        if self.attended_minutes > self.training_duration_minutes:
            errors["attended_minutes"] = "Qatnashgan daqiqa mashg'ulot davomiyligidan katta bo'lishi mumkin emas."
        if self.attendance_status not in dict(self.STATUS_CHOICES):
            errors["attendance_status"] = "Davomad holati noto'g'ri yuborildi."
        if self.injury_status not in dict(self.INJURY_CHOICES):
            errors["injury_status"] = "Jarohat holati noto'g'ri yuborildi."
        if self.physical_condition not in dict(self.PHYSICAL_CHOICES):
            errors["physical_condition"] = "Jismoniy holat noto'g'ri yuborildi."
        if self.activity_level not in dict(self.ACTIVITY_CHOICES):
            errors["activity_level"] = "Faollik holati noto'g'ri yuborildi."
        if self.discipline not in dict(self.DISCIPLINE_CHOICES):
            errors["discipline"] = "Intizom holati noto'g'ri yuborildi."
        if errors:
            raise ValidationError(errors)

    @property
    def participation_percent(self):
        if not self.training_duration_minutes:
            return 0
        return round((self.attended_minutes / self.training_duration_minutes) * 100, 2)


class TeamStatistic(TimeStampedModel):
    title = models.CharField(max_length=120)
    metric_value = models.CharField(max_length=50)
    accent = models.CharField(max_length=20, default="blue")
    change_text = models.CharField(max_length=80, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "title"]
        verbose_name = "jamoa statistikasi"
        verbose_name_plural = "jamoa statistikasi"

    def __str__(self):
        return self.title


class PlayerStatistic(TimeStampedModel):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="statistics")
    matches_played = models.PositiveIntegerField(default=0)
    goals = models.PositiveIntegerField(default=0)
    assists = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0)

    class Meta:
        verbose_name = "futbolchi statistikasi"
        verbose_name_plural = "futbolchi statistikasi"

    def __str__(self):
        return f"{self.player.full_name} statistikasi"
