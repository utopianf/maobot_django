# Generated by Django 2.0.1 on 2019-05-25 00:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ircimages', '0005_auto_20180610_0056'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(max_length=50, verbose_name='Tag')),
            ],
        ),
    ]
