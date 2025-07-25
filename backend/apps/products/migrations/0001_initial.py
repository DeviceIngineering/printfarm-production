# Generated by Django 4.2.7 on 2025-07-19 00:58

from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('moysklad_id', models.CharField(db_index=True, max_length=36, unique=True)),
                ('article', models.CharField(db_index=True, max_length=255)),
                ('name', models.CharField(max_length=500)),
                ('description', models.TextField(blank=True)),
                ('product_group_id', models.CharField(blank=True, max_length=36)),
                ('product_group_name', models.CharField(blank=True, max_length=255)),
                ('current_stock', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=10)),
                ('sales_last_2_months', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=10)),
                ('average_daily_consumption', models.DecimalField(decimal_places=4, default=Decimal('0'), max_digits=10)),
                ('product_type', models.CharField(choices=[('new', 'Новая позиция'), ('old', 'Старая позиция'), ('critical', 'Критическая позиция')], default='new', max_length=20)),
                ('days_of_stock', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('production_needed', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=10)),
                ('production_priority', models.IntegerField(default=0)),
                ('last_synced_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-production_priority', 'article'],
            },
        ),
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('image', models.ImageField(blank=True, null=True, upload_to='products/')),
                ('thumbnail', models.ImageField(blank=True, null=True, upload_to='products/thumbnails/')),
                ('moysklad_url', models.URLField(blank=True, max_length=500)),
                ('is_main', models.BooleanField(default=False)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='products.product')),
            ],
            options={
                'ordering': ['-is_main', 'created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['product_type', 'production_priority'], name='products_pr_product_f66608_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['current_stock', 'product_type'], name='products_pr_current_b62db8_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['article'], name='products_pr_article_76912c_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['moysklad_id'], name='products_pr_moyskla_6e1c9f_idx'),
        ),
    ]
