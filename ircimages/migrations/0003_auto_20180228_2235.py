# Generated by Django 2.0.1 on 2018-02-28 22:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ircimages', '0002_auto_20180228_2234'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='image',
            field=models.ImageField(null=True, upload_to=''),
        ),
        migrations.AlterField(
            model_name='image',
            name='thumb',
            field=models.ImageField(null=True, upload_to='thumb/'),
        ),
    ]
