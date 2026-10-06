from django.contrib import admin

from .models import Choice, Course, Enrollment, Group, Lesson, Question, QuizAttempt


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    show_change_link = True


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "price", "is_published", "created_at")
    list_editable = ("price", "is_published")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [LessonInline, QuestionInline]


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4
    max_num = 6


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "course", "order")
    list_filter = ("course",)
    inlines = [ChoiceInline]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "is_active", "phone", "created_at")
    list_editable = ("is_active",)
    list_filter = ("course", "is_active")
    search_fields = ("student__username", "student__first_name", "student__last_name", "phone")
    actions = ["kursni_ochish", "kursni_yopish"]

    @admin.action(description="Tanlangan yozuvlar uchun kursga kirishni ochish")
    def kursni_ochish(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Tanlangan yozuvlar uchun kursga kirishni yopish")
    def kursni_yopish(self, request, queryset):
        queryset.update(is_active=False)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("name", "course", "created_at")
    filter_horizontal = ("members",)


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "score", "total", "created_at")
    list_filter = ("course",)
    search_fields = ("student__username",)
