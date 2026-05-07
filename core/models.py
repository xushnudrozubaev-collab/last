from django.contrib.auth.models import User
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
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["-match_date", "-match_time"]
        verbose_name = "o'yin"
        verbose_name_plural = "o'yinlar"

    def __str__(self):
        return f"{self.home_team} vs {self.away_team}"

    def get_absolute_url(self):
        return reverse("match_detail", args=[self.pk])


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
