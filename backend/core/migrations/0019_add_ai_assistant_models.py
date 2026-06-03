# Generated manually for AI Assistant models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0018_remove_sample_wording'),
    ]

    operations = [
        migrations.CreateModel(
            name='AIConversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(default='Yangi suhbat', max_length=200)),
                ('is_active', models.BooleanField(default=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ai_conversations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'AI suhbat',
                'verbose_name_plural': 'AI suhbatlar',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='AIMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('role', models.CharField(choices=[('user', 'Foydalanuvchi'), ('assistant', 'AI Yordamchi')], max_length=20)),
                ('content', models.TextField()),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='core.aiconversation')),
            ],
            options={
                'verbose_name': 'AI xabar',
                'verbose_name_plural': 'AI xabarlar',
                'ordering': ['created_at'],
            },
        ),
    ]
