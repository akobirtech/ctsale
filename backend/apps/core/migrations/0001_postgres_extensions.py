"""PostgreSQL kengaytmalari.

Ular migratsiya orqali yaratiladi, chunki test bazasi har safar
noldan quriladi — qo'lda yaratilgan kengaytmalar u yerda bo'lmaydi
va trigram qidiruvi testlarda ishlamay qolardi.
"""

from django.contrib.postgres.operations import TrigramExtension, UnaccentExtension
from django.db import migrations


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        TrigramExtension(),
        UnaccentExtension(),
    ]
