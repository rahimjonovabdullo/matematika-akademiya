from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


class Course(models.Model):
    KIND_CHOICES = [
        ("kurs", "Kurs"),
        ("test", "Test"),
    ]
    CATEGORY_CHOICES = [
        ("asosiy", "Asosiy"),
        ("milliy", "Milliy Sertifikat"),
        ("attestatsiya", "Attestatsiya"),
        ("sat", "SAT"),
    ]

    title = models.CharField("Nomi", max_length=200)
    slug = models.SlugField("Slug", unique=True, help_text="Manzilda ko'rinadigan qism, masalan: algebra-asoslari")
    kind = models.CharField("Turi", max_length=10, choices=KIND_CHOICES, default="kurs")
    description = models.TextField("Tavsif", blank=True)
    category = models.CharField("Toifa", max_length=20, choices=CATEGORY_CHOICES, default="asosiy")
    price = models.PositiveIntegerField("Narxi (so'm)", default=0)
    duration_minutes = models.PositiveIntegerField(
        "Davomiyligi (daqiqa)",
        default=0,
        help_text="Test uchun vaqt. 0 bo'lsa ko'rsatilmaydi.",
    )
    is_published = models.BooleanField("Sahifada ko'rinsinmi", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Kurs"
        verbose_name_plural = "Kurslar"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("course_detail", args=[self.slug])


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons", verbose_name="Kurs")
    title = models.CharField("Sarlavha", max_length=200)
    video_url = models.URLField("Video havolasi (YouTube va h.k.)", blank=True)
    content = models.TextField("Dars matni / izoh", blank=True)
    order = models.PositiveIntegerField("Tartib raqami", default=0)
    is_free_preview = models.BooleanField("To'lovsiz ham ko'rinadimi (demo)", default=False)

    class Meta:
        verbose_name = "Dars"
        verbose_name_plural = "Darslar"
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.course.title} — {self.title}"


class Question(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="questions", verbose_name="Kurs")
    text = models.TextField("Savol matni")
    order = models.PositiveIntegerField("Tartib raqami", default=0)

    class Meta:
        verbose_name = "Savol"
        verbose_name_plural = "Savollar"
        ordering = ["order", "id"]

    def __str__(self):
        return self.text[:60]


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices", verbose_name="Savol")
    text = models.CharField("Variant matni", max_length=300)
    is_correct = models.BooleanField("To'g'ri javobmi", default=False)

    class Meta:
        verbose_name = "Javob varianti"
        verbose_name_plural = "Javob variantlari"

    def __str__(self):
        return self.text


class Enrollment(models.Model):
    """Bir o'quvchining bir kursga yozilgani va kirish huquqi (admin tomonidan
    qo'lda ochiladi — to'lov tizimi ulanmaguncha shu tartib ishlatiladi)."""

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="enrollments", verbose_name="O'quvchi")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments", verbose_name="Kurs")
    is_active = models.BooleanField("Kursga kirish ochilganmi", default=False)
    phone = models.CharField("Telefon raqami", max_length=30, blank=True)
    note = models.CharField("Izoh (masalan, to'lov cheki haqida)", max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ro'yxatga olish"
        verbose_name_plural = "Ro'yxatga olishlar"
        unique_together = ("student", "course")

    def __str__(self):
        holat = "ochiq" if self.is_active else "yopiq"
        return f"{self.student.username} — {self.course.title} ({holat})"


class QuizAttempt(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="attempts", verbose_name="O'quvchi")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="attempts", verbose_name="Kurs")
    score = models.PositiveIntegerField("To'g'ri javoblar soni")
    total = models.PositiveIntegerField("Jami savollar soni")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Test natijasi"
        verbose_name_plural = "Test natijalari"
        ordering = ["-created_at"]

    @property
    def percent(self):
        if not self.total:
            return 0
        return round(self.score * 100 / self.total)

    def __str__(self):
        return f"{self.student.username} — {self.course.title}: {self.score}/{self.total}"


class Group(models.Model):
    """O'qituvchi tomonidan yaratiladigan o'quvchilar guruhi."""

    name = models.CharField("Nomi", max_length=150)
    course = models.ForeignKey(
        Course, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="groups", verbose_name="Bog'liq kurs"
    )
    members = models.ManyToManyField(
        User, blank=True, related_name="study_groups", verbose_name="A'zolar"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Guruh"
        verbose_name_plural = "Guruhlar"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
