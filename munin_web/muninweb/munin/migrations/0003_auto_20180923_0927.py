# Generated by Django 2.1.1 on 2018-09-23 09:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('munin', '0002_auto_20180923_0925'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='last_crawled_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='seed',
            name='last_check',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='seed',
            name='state',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]