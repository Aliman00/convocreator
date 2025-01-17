# Generated by Django 5.0.6 on 2024-07-01 06:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('convotemplates', '0003_alter_convooption_next_screen_alter_convooption_text'),
    ]

    operations = [
        migrations.AddField(
            model_name='convooption',
            name='stf_reference',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='convoscreen',
            name='left_dialog',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='convotemplate',
            name='stf_mode',
            field=models.BooleanField(default=False),
        ),
    ]
