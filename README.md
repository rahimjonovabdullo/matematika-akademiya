# Matematika Akademiya

Django asosida qurilgan ta'lim platformasi: kurslar, darslar, testlar,
o'quvchi kabineti va admin panel.

## 1. Kompyuterda sinab ko'rish (ixtiyoriy)

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Brauzerda `http://127.0.0.1:8000` — sayt, `http://127.0.0.1:8000/admin` — admin panel.

## 2. GitHub'ga joylash

```bash
git init
git add .
git commit -m "Birinchi versiya"
git branch -M main
git remote add origin https://github.com/FOYDALANUVCHI_NOMI/akademiya.git
git push -u origin main
```

(`FOYDALANUVCHI_NOMI` o'rniga o'z GitHub loginingizni yozing. Avval
github.com'da bo'sh repozitoriy oching, keyin shu buyruqlarni bering.)

## 3. Railway'da yangi loyiha ochish

1. Railway panelida **New Project → Deploy from GitHub repo** tanlang, shu
   repozitoriyni tanlang. Bu botingiz turgan loyihaga tegmaydi, alohida
   yangi loyiha ochiladi.
2. Shu loyiha ichida **New → Database → PostgreSQL** qo'shing. Railway
   `DATABASE_URL` ni avtomatik ulaydi.
3. Ilova xizmatida (Settings → Variables) quyidagilarni qo'shing:
   - `SECRET_KEY` — istalgan uzun tasodifiy satr
   - `DEBUG` — `False`
4. Birinchi joylashdan keyin **superuser** (admin) yaratish uchun Railway
   loyihasida "Shell" yoki CLI orqali:
   ```bash
   railway run python manage.py createsuperuser
   ```
5. **Settings → Networking** bo'limida domeningizni (masalan
   `matematikaakademiya.uz`) qo'shing va ko'rsatilgan DNS yozuvini domen
   provayderingizda sozlang.

## 4. Birinchi kursni qo'shish

`/admin` ga kiring → **Kurslar → Qo'shish**. Kurs ichida darslar va
savollarni ham shu yerdan qo'shasiz (sahifaning pastida "Darslar" va
"Savollar" bo'limlari chiqadi).

## Hozircha yo'q, keyin qo'shiladi

- Avtomatik to'lov (Click/Payme) — hozircha o'quvchi telefon raqamini
  qoldiradi, siz to'lovni tekshirib, admin panelda "Kursga kirish"ni
  qo'lda yoqasiz (Enrollment → is_active).
- SMS orqali tasdiqlash.
