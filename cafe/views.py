from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from .models import Cafe, CafeImage, Review, ReviewImage, Tag
from .utils import upload_to_r2
from django.db.models import Avg, Subquery, OuterRef, Count, Q

def cafe_list(request):
    # --- GET パラメータ ---
    q = request.GET.get('q')              # 店名検索
    tag = request.GET.get('tag')          # タグ絞り込み
    place = request.GET.get('place')      # 場所（最寄り or 住所）
    page = int(request.GET.get('page', 1))
    per_page = 20   # ← ここが重要！

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

    # --- 場所絞り込み（最寄り + 住所） ---
    if place:
        cafes = cafes.filter(
            Q(nearest_station__icontains=place) |
            Q(address__icontains=place)
        )

    # --- デフォルト：評価順（高い順） ---
    cafes = cafes.order_by('-avg_rating')

    # タグ一覧（絞り込み用）
    tags = Tag.objects.all()

    page = int(request.GET.get('page', 1))
    start = (page - 1) * per_page
    end = start + per_page
    cafes_page = cafes[start:end]
    has_more = cafes.count() > end
    total_count = cafes.count()

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