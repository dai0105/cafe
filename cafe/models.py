from django.db import models

class Tag(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Cafe(models.Model):
    # 基本情報
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=300)
    description = models.TextField(blank=True)

    # 営業情報
    opening_hours = models.CharField(max_length=200, blank=True)
    holiday = models.CharField(max_length=200, blank=True)

    # 設備
    has_wifi = models.BooleanField(default=False)
    has_power = models.BooleanField(default=False)
    seats = models.IntegerField(null=True, blank=True)

    # SNS / Web
    website = models.URLField(blank=True)
    instagram = models.URLField(blank=True)

    menu1 = models.CharField("おすすめメニュー1", max_length=100, blank=True, null=True)
    menu2 = models.CharField("おすすめメニュー2", max_length=100, blank=True, null=True)
    menu3 = models.CharField("おすすめメニュー3", max_length=100, blank=True, null=True)

    # タグ（焼き菓子・席間広い・朝ごはん etc）
    tags = models.ManyToManyField(Tag, blank=True)

    phone = models.CharField(max_length=20, blank=True, null=True)

    catch_copy = models.CharField(max_length=100, blank=True)
    nearest_station = models.CharField(max_length=100, blank=True)

    # 並び順用（weighted random）
    weight = models.FloatField(default=1.0)

    # 新規ブースト用
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class CafeImage(models.Model):
    cafe = models.ForeignKey(Cafe, on_delete=models.CASCADE, related_name='images')
    image_url = models.URLField()

    IMAGE_TYPE_CHOICES = (
        ('main', 'メイン画像'),
        ('sub', 'サブ画像'),
    )
    image_type = models.CharField(max_length=10, choices=IMAGE_TYPE_CHOICES, default='sub')

    order = models.PositiveIntegerField(default=1)

    caption = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.cafe.name} - {self.image_type} - {self.order}"
    
class Review(models.Model):
    cafe = models.ForeignKey(Cafe, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(default=5)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.cafe.name} - ★{self.rating}"


class ReviewImage(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='images')
    image_url = models.URLField()

    IMAGE_TYPE_CHOICES = (
        ('main', 'メイン画像'),
        ('sub', 'サブ画像'),
    )
    image_type = models.CharField(max_length=10, choices=IMAGE_TYPE_CHOICES, default='sub')

    order = models.PositiveIntegerField(default=1)
    caption = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Review {self.review.id} - {self.image_type} - {self.order}"