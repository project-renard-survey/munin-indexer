# Generated by Django 2.1.1 on 2018-12-03 20:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('munin', '0007_post_jobid'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='retry_count',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
