# Munin - a social media archiver

This tool will monitor open Facebook, Instagram and VKontakte account seeds for new posts and archive those posts. Posts are archived in the WARC file format using the excellent Squidwarc package. A playback tool and a simple dashboard is available to monitor collections.

<img src="https://user-images.githubusercontent.com/19284/49699663-3e337b80-fbd4-11e8-8282-035ea7f219ba.png" alt="Munin dashboard screenshot">

# System overview

Munin builds on great software by other people. Indexing of post items is done in [snscrape](https://github.com/JustAnotherArchivist/snscrape). Archiving of individual pages is done with [Squidwarc](https://n0tan3rd.github.io/Squidwarc/). Playback of WARC files is enabled by [pywb](https://pywb.readthedocs.io/en/latest/).

<img src="https://user-images.githubusercontent.com/19284/50910651-8392d500-142e-11e9-9133-8766249c09b8.png" alt="System overview - a Django application manages seeds and post URL:s in a PostgreSQL database. A queue for indexing finds more post URLs for the seeds. A queue for archiving makes sure post URLs are archived."/>

# Install

Create an empty data directory for postgres called data.

`$ mkdir data`

Copy `example_env_file` to env_file and update it with your settings (no change necessary if you only plan to try it out).

Start everything:

`$ docker-compose up -d`

The first time the application starts it can take a while (several minutes) before the application becomes available. You can monitor progress by watching the docker logs.

Set up a superuser when the application is up (it will ask you for details to create an administrator):

`$ docker-compose exec web python manage.py createsuperuser`

Login to the admin dashboard with the newly created superuser at http://0.0.0.0:4444/admin

Start by adding your first Collection item in the admin interface. Then add one or more seed URLs to the collection (e.g. https://www.facebook.com/visitberlin/). You can bulk add multiple seeds (one per line) fron the dashboard.

After a couple of minutes the crawler should have discovered public posts and archived them. You can monitor the dashboard for new items added to the collection. Clicking the play icon will open the archived page. All archived pages are available for playback from http://0.0.0.0:4445/munin/
