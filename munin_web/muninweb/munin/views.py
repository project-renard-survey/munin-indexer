from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from munin.models import *
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
import subprocess
import pytz
import os
from datetime import datetime, timezone, timedelta
import math
from random import random
from munin.extras import get_uid
import csv
from django.http import StreamingHttpResponse

@login_required
def bulk_add(request):

    collections = Collection.objects.all()

    if len(collections) == 0:
        messages.error(request, "There are no collections to add seeds to. Please create a collection in the <a href='/admin/munin/collection/'>admin interface</a> first.")
        return render(request, 'bulk_add.html', context={"collections":collections})


    if request.POST:
        seedstxt =  request.POST.get("seeds")
        collection_id = int(request.POST.get("collection"))
        
        if not collection_id > 0:
            messages.error(request, 'No collection selected.')
            return render(request, 'bulk_add.html', context={"collections":collections}) 
        
        count = 0

        for seed in seedstxt.splitlines():
            try:
                obj = Seed.objects.get(seed=seed.strip())
                print("Skipping " + seed)
            except Seed.DoesNotExist:
                obj = Seed(seed=seed.strip(), collection_id=collection_id)
                obj.save()
                count += 1
                print("Added " + seed)

        messages.success(request, f"Added {count} seeds for collection {collection_id}")

    return render(request, 'bulk_add.html', context=locals())


#@login_required
def export_seed_data(request):
    seeds = Seed.objects.annotate(post_count=Count('post')).order_by("seed")
    response = HttpResponse(content_type='text/csv')
    writer = csv.writer(response, quotechar='"', quoting=csv.QUOTE_ALL)
    writer.writerow(["collection", "collection_id", "seed_id", "seed", "post_count", "deactivated"])
    for seed in seeds:
        writer.writerow([seed.collection.name, seed.collection.id, seed.id, seed.seed, seed.post_count, seed.deactivated])

    return response


@login_required
def index(request):
    #stats for dashboard - also see chart script below
    post_queue_length = Post.objects.filter(state=2).count()
    seed_queue_length = Seed.objects.filter(state=2).count()

    warc_file_count = Post.objects.filter(state=1, warc_size__gt=0).count() 

    warc_size_sum = Post.objects.aggregate(Sum("warc_size"))["warc_size__sum"] or 0
    archive_size = round(warc_size_sum / 1024 / 1024 / 1024, 1)

    now = datetime.now(pytz.timezone(os.environ["TZ"]))
    last_week_timedelta = now - timedelta(days=7)

    last_posts = Post.objects.filter(state=1, last_crawled_at__gt=last_week_timedelta).order_by("-last_crawled_at")[:10]

    crawl_error_count = Post.objects.exclude(last_error__isnull=True).exclude(last_error__exact="").count()

    hostname = os.environ["HOSTNAME"]

    return render(request, 'dashboard.html', context=locals())


def hours_ago(timestamp):
    now = datetime.now(pytz.timezone(os.environ["TZ"]))
    delta = now - timestamp
    return (delta.days*24) + int(delta.seconds/3600)


@login_required
def chart_script(request):
    now = datetime.now(pytz.timezone(os.environ["TZ"]))
    stats = Stats.objects.all().order_by("-id")[:96] # last 4 days worth of stat items (24 x 4)
    stats = list(reversed(stats))

    if len(stats) > 0:
        post_queue_last7 = [stat.post_crawl_queue for stat in stats]
        #post_queue_last7 = [int(random()*1200) for stat in stats]
        post_queue_last7_max = int(max(post_queue_last7) + max(post_queue_last7) *0.1)
        post_queue_last7 = ', '.join(map(str,post_queue_last7))

        seed_queue_last7 = [stat.seed_crawl_queue for stat in stats]
        seed_queue_last7_max = int(max(seed_queue_last7) + max(seed_queue_last7) *0.1)
        seed_queue_last7 = ', '.join(map(str,seed_queue_last7))

        warcs_created_last7 = [stat.warcs_created for stat in stats]
        #warcs_created_last7 = [int(random()*100) for stat in stats]
        warcs_created_last7_max = int(max(warcs_created_last7) + max(warcs_created_last7) *0.1)
        warcs_created_last7 = ', '.join(map(str, warcs_created_last7))
        
        stat_labels = [hours_ago(stat.created_at) for stat in stats]
        stat_labels = ', '.join(map(str, stat_labels))
        stat_dates = [stat.id for stat in stats]

        chart_max = int(math.ceil(max([post_queue_last7_max, warcs_created_last7_max, seed_queue_last7_max]) / 100.0)) * 100
        return render(request, 'chart_script.js',  content_type="text/javascript", context=locals())
    else:
        return HttpResponse("No stats yet")




@login_required
def collection_meta(request, collection_id=None):
    """Render collection metadata in plain text or XML.
    """

    collection = get_object_or_404(Collection, pk=collection_id) 
    r = HttpResponse(content_type='text/plain')

    for seed in collection.seed_set.order_by("seed"):
        r.write(seed.seed + "\n")

    return r


@csrf_exempt
@require_http_methods(["POST"])
def add_post_url_for_seed(request, seed_id=None):

    try:
        seed = Seed.objects.get(pk=seed_id)
    except Seed.DoesNotExist:
        raise Http404("No Seed matches the given query.")

    # add url if it doesnt exist already
    try:
        post_url = request.POST.get("post_url")

        # compute uid
        uid = get_uid(post_url)
        post = Post.objects.get(seed=seed, uid=uid)
    except Post.DoesNotExist:
        p = Post(seed=seed, url=post_url, uid=uid)
        p.save()
        return HttpResponse(f"New post url: {post_url}, UID: {uid}")
    except Exception:
        raise Http404("No post url.")
    
    return HttpResponseForbidden(f"Already exists: {uid} {post_url}")


@csrf_exempt
@require_http_methods(["POST"])
def add_post_url(request):

    try:
        seed_url = request.POST.get("seed_url")
        seed = Seed.objects.get(seed=seed_url)
    except Seed.DoesNotExist:
        print("No seed")
        raise Http404("No Seed matches the given query.")

    try:
        post_url = request.POST.get("post_url")
        uid = get_uid(post_url)
        print(f"Trying to find post uid {uid} for {seed_url}")
        if not Post.objects.filter(seed=seed, uid=uid).exists():
            p = Post(seed=seed, uid=uid, url=post_url)
            p.save()
            print(f"Added {p.id} {uid}")
            return HttpResponse(f"New post url: {uid}: {post_url}")
    except Exception as e:
        print("Exception")
        print(e)
        raise Http404(f"Exception occurred. {e}")
    
    return HttpResponseForbidden(f"Already exists: {uid} {post_url} for {seed}")



@csrf_exempt
@require_http_methods(["POST"])
def dequeue_seed(request):

    try:
        seed_url = request.POST.get("seed_url")
        seed = Seed.objects.get(seed=seed_url)
        seed.dequeue()
    except Seed.DoesNotExist:
        raise Http404("dequeue_seed: No Seed matches the given query.")

    return HttpResponse(f"Dequeued: {seed_url}")



@csrf_exempt
@require_http_methods(["POST"])
def dequeue_post_url(request):

    try:
        post_url = request.POST.get("post_url")
        seed_id = request.POST.get("seed_id")
        warc_path = request.POST.get("warc_path")
        warc_size = request.POST.get("warc_size")
        last_error = request.POST.get("last_error")
        seed = Seed.objects.get(id=int(seed_id))
        post = Post.objects.get(seed=seed, url=post_url)

        post.dequeue(warc_path=warc_path, warc_size=warc_size, last_error=last_error)

    except Seed.DoesNotExist:
        print("dequeue_post_url: No Seed matches the given query.")
        raise Http404("dequeue_post_url: No Seed matches the given query.")
    except Post.DoesNotExist:
        print("dequeue_post_url: No Post matches the given query.")
        raise Http404("dequeue_post_url: No Post matches the given query.")
    except Exception as e: 
        print(e)

    return HttpResponse(f"Dequeued: {post_url}")
