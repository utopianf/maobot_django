# Generated by Django 2.0.1 on 2018-02-28 22:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('irclog', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='log',
            options={'ordering': ['-id']},
        ),
    ]