from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('nutrition', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='FoodLog',
        ),
    ]
