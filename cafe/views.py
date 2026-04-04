from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from .models import Cafe, CafeImage, Review, ReviewImage, Tag
from .utils import upload_to_r2
from django.db.models import Avg, Subquery, OuterRef, Count, Q
from datetime import datetime, timezone


def calculate_weight(cafe):
    # created_at が None の場合に備える
    if not cafe.created_at:
        days_since_created = 9999
    else:
        days_since_created = (datetime.now(timezone.utc) - cafe.created_at).days

    # 新規ブースト
    if days_since_created <= 7:
        new_store_boost = 20
    elif days_since_created <= 30:
        new_store_boost = 10
    else:
        new_store_boost = 0

    # None 対策
    review_count = cafe.review_count or 0
    avg_rating = cafe.avg_rating or 0

    weight = (
        new_store_boost +
        review_count * 2 +
        avg_rating * 1
    )

    return max(weight, 1)



def cafe_list(request):
    # --- GET パラメータ ---
    q = request.GET.get('q')
    tag = request.GET.get('tag')
    place = request.GET.get('place')
    page = int(request.GET.get('page', 1))
    per_page = 20

    # --- メイン画像のサブクエリ ---
    main_image_subquery = CafeImage.objects.filter(
        cafe=OuterRef('pk'),
        image_type='main'
    ).values('image_url')[:1]

    # --- ベースクエリ ---
    cafes = Cafe.objects.annotate(
        avg_rating=Avg('reviews__rating'),
        main_image_url=Subquery(main_image_subquery),
        review_count=Count('reviews')
    )

    # --- 店名検索 ---
    if q:
        cafes = cafes.filter(name__icontains=q)

    # --- タグ絞り込み ---
    if tag:
        cafes = cafes.filter(tags__id=tag)

    # --- 場所絞り込み ---
    if place:
        cafes = cafes.filter(
            Q(nearest_station__icontains=place) |
            Q(address__icontains=place)
        )

    # --- デフォルト：勢い順（Weighted Random） ---
    import random

    weighted_list = []
    for cafe in cafes:
        weight = calculate_weight(cafe)

        # ランダム揺らしを加えてソート用スコアを作る
        random_factor = random.uniform(0.8, 1.2)
        final_score = weight * random_factor

        weighted_list.append((final_score, cafe))

    # スコアの高い順にソート
    weighted_list.sort(key=lambda x: x[0], reverse=True)

    # カフェだけ取り出す
    sorted_cafes = [c for score, c in weighted_list]

    # --- ページネーション ---
    start = (page - 1) * per_page
    end = start + per_page
    cafes_page = sorted_cafes[start:end]

    has_more = len(sorted_cafes) > end
    total_count = len(sorted_cafes)

    tags = Tag.objects.all()

    return render(request, 'cafe/list.html', {
        'cafes': cafes_page,
        'has_more': has_more,
        'page': page,
        'tags': tags,
        'q': q,
        'selected_tag': tag,
        'place': place,
        'total_count': total_count,
    })


def cafe_detail(request, cafe_id):
    cafe = get_object_or_404(Cafe, id=cafe_id)

    # -------------------------
    # 口コミ投稿（POST）
    # -------------------------
    if request.method == "POST":
        review = Review.objects.create(
            cafe=cafe,
            rating=request.POST["rating"],
            comment=request.POST["comment"],
        )

        # 画像があればアップロード
        for img in request.FILES.getlist("images"):
            image_url = upload_to_r2(img, folder=f"reviews/{review.id}/")

            ReviewImage.objects.create(
                review=review,
                image_url=image_url,
                image_type="sub",  # とりあえず全部サブ扱い
                order=1,
            )

        return redirect("cafe_detail", cafe_id=cafe.id)

    # -------------------------
    # 並び替え（GET）
    # -------------------------
    sort = request.GET.get("sort", "new")  # デフォルトは新着順

    if sort == "new":
        all_reviews = cafe.reviews.all().order_by("-created_at")
    elif sort == "old":
        all_reviews = cafe.reviews.all().order_by("created_at")
    elif sort == "high":
        all_reviews = cafe.reviews.all().order_by("-rating", "-created_at")
    elif sort == "low":
        all_reviews = cafe.reviews.all().order_by("rating", "-created_at")
    else:
        all_reviews = cafe.reviews.all().order_by("-created_at")

    # 最初の5件だけ
    initial_reviews = all_reviews[:5]
    total_count = all_reviews.count()

    # ★ 星の平均
    avg_rating = all_reviews.aggregate(avg=Avg("rating"))["avg"]

    return render(
        request,
        "cafe/cafe_detail.html",
        {
            "cafe": cafe,
            "initial_reviews": initial_reviews,
            "total_count": total_count,
            "avg_rating": avg_rating,
            "sort": sort,  # ← 並び替えタブ用
        },
    )


def load_more_reviews(request, cafe_id):
    sort = request.GET.get("sort", "new")
    offset = int(request.GET.get("offset", 0))

    if sort == "new":
        reviews = Review.objects.filter(cafe_id=cafe_id).order_by("-created_at")
    elif sort == "old":
        reviews = Review.objects.filter(cafe_id=cafe_id).order_by("created_at")
    elif sort == "high":
        reviews = Review.objects.filter(cafe_id=cafe_id).order_by("-rating", "-created_at")
    elif sort == "low":
        reviews = Review.objects.filter(cafe_id=cafe_id).order_by("rating", "-created_at")
    else:
        reviews = Review.objects.filter(cafe_id=cafe_id).order_by("-created_at")

    reviews = reviews[offset:offset+5]

    return render(request, "cafe/review_items.html", {
        "reviews": reviews
    })


def calculate_weight(store, user_tags):
    # 経過日数
    days_since_created = (datetime.now(timezone.utc) - store.created_at).days

    # 新規ブースト
    if days_since_created <= 7:
        new_store_boost = 20
    elif days_since_created <= 30:
        new_store_boost = 10
    else:
        new_store_boost = 0

    # タグ一致度（store.tags が list or set 前提）
    tag_match_score = len(set(store.tags).intersection(user_tags))

    # 最終スコア
    weight = (
        new_store_boost +
        tag_match_score * 5 +
        store.review_count * 2 +
        store.rating * 1
    )

    return max(weight, 1)  # 重み0だとランダム抽選できないので最低1