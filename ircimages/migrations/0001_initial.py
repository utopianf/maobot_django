# Generated by Django 2.2.1 on 2019-05-25 00:44

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('irclog', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ImageSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=20, verbose_name='title')),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(max_length=50, verbose_name='Tag')),
            ],
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('original_url', models.URLField(null=True)),
                ('caption', models.TextField(max_length=1000, null=True, verbose_name='Caption')),
                ('extension', models.CharField(max_length=10, null=True, verbose_name='Extension')),
                ('image', models.ImageField(null=True, upload_to='')),
                ('thumb', models.ImageField(null=True, upload_to='thumb/')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('image_set', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='images', to='ircimages.ImageSet')),
                ('related_log', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='images', to='irclog.Log')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
