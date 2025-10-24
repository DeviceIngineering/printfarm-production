"""
Тесты для ArticleNormalizer

Проверяет корректность нормализации артикулов из различных источников.
"""
from django.test import TestCase
from apps.core.utils.article_normalizer import ArticleNormalizer, normalize_article


class ArticleNormalizerTestCase(TestCase):
    """Тесты для класса ArticleNormalizer"""

    def test_normalize_basic(self):
        """Тест базовой нормализации"""
        self.assertEqual(ArticleNormalizer.normalize("N323-13W"), "N323-13W")
        self.assertEqual(ArticleNormalizer.normalize("496-51850"), "496-51850")

    def test_normalize_with_spaces(self):
        """Тест нормализации с пробелами"""
        self.assertEqual(ArticleNormalizer.normalize("  N323-13W  "), "N323-13W")
        self.assertEqual(ArticleNormalizer.normalize("N323 -13W"), "N323 -13W")
        self.assertEqual(ArticleNormalizer.normalize("N323  -  13W"), "N323 - 13W")

    def test_normalize_with_different_dashes(self):
        """Тест нормализации с различными типами тире"""
        # En dash (–)
        self.assertEqual(ArticleNormalizer.normalize("496–51850"), "496-51850")
        # Em dash (—)
        self.assertEqual(ArticleNormalizer.normalize("496—51850"), "496-51850")
        # Minus sign (−)
        self.assertEqual(ArticleNormalizer.normalize("496−51850"), "496-51850")
        # Figure dash (‒)
        self.assertEqual(ArticleNormalizer.normalize("496‒51850"), "496-51850")

    def test_normalize_empty_and_none(self):
        """Тест нормализации пустых значений"""
        self.assertEqual(ArticleNormalizer.normalize(None), "")
        self.assertEqual(ArticleNormalizer.normalize(""), "")
        self.assertEqual(ArticleNormalizer.normalize("   "), "")

    def test_normalize_with_invisible_characters(self):
        """Тест нормализации с невидимыми символами"""
        # Zero-width space
        self.assertEqual(ArticleNormalizer.normalize("N323\u200b-13W"), "N323-13W")
        # Non-breaking space
        self.assertEqual(ArticleNormalizer.normalize("N323\xa0-13W"), "N323-13W")

    def test_normalize_case_sensitive(self):
        """Тест что регистр сохраняется"""
        self.assertEqual(ArticleNormalizer.normalize("N323-13W"), "N323-13W")
        self.assertEqual(ArticleNormalizer.normalize("n323-13w"), "n323-13w")

    def test_normalize_case_insensitive(self):
        """Тест регистронезависимой нормализации"""
        self.assertEqual(
            ArticleNormalizer.normalize_case_insensitive("N323-13W"),
            "n323-13w"
        )
        self.assertEqual(
            ArticleNormalizer.normalize_case_insensitive("N323-13W"),
            ArticleNormalizer.normalize_case_insensitive("n323-13w")
        )

    def test_normalize_batch(self):
        """Тест пакетной нормализации"""
        articles = ["N323-13W ", "496–51850", "  abc  ", None]
        result = ArticleNormalizer.normalize_batch(articles)

        self.assertEqual(result["N323-13W "], "N323-13W")
        self.assertEqual(result["496–51850"], "496-51850")
        self.assertEqual(result["  abc  "], "abc")
        self.assertEqual(result[None], "")

    def test_normalize_real_world_examples(self):
        """Тест реальных примеров из проекта"""
        # Примеры из Excel
        self.assertEqual(ArticleNormalizer.normalize("423-51412"), "423-51412")

        # Примеры из МойСклад с различными тире
        self.assertEqual(ArticleNormalizer.normalize("496–51850"), "496-51850")

        # Примеры с пробелами по краям
        self.assertEqual(ArticleNormalizer.normalize(" N323-13W "), "N323-13W")

    def test_normalize_special_cases(self):
        """Тест специальных случаев"""
        # Числовой артикул
        self.assertEqual(ArticleNormalizer.normalize(12345), "12345")

        # Артикул с точкой
        self.assertEqual(ArticleNormalizer.normalize("ABC.123"), "ABC.123")

        # Артикул с подчеркиванием
        self.assertEqual(ArticleNormalizer.normalize("ABC_123"), "ABC_123")

    def test_normalize_cache(self):
        """Тест кэширования"""
        # Очищаем кэш перед тестом
        ArticleNormalizer.clear_cache()

        # Первый вызов - промах кэша
        result1 = ArticleNormalizer.normalize("N323-13W")

        # Второй вызов - попадание в кэш
        result2 = ArticleNormalizer.normalize("N323-13W")

        self.assertEqual(result1, result2)

        # Проверяем информацию о кэше
        cache_info = ArticleNormalizer.get_cache_info()
        self.assertGreaterEqual(cache_info['hits'], 1)
        self.assertGreaterEqual(cache_info['size'], 1)

    def test_normalize_article_function(self):
        """Тест функции-обертки normalize_article"""
        self.assertEqual(normalize_article("N323-13W "), "N323-13W")
        self.assertEqual(normalize_article("496–51850"), "496-51850")
        self.assertEqual(normalize_article(None), "")


class ArticleNormalizerPerformanceTestCase(TestCase):
    """Тесты производительности ArticleNormalizer"""

    def test_normalize_performance_with_cache(self):
        """Тест производительности с кэшированием"""
        import time

        # Очищаем кэш
        ArticleNormalizer.clear_cache()

        # Тестовые данные
        articles = [f"N{i}-13W" for i in range(1000)]

        # Первый проход - заполнение кэша
        start_time = time.time()
        for article in articles:
            ArticleNormalizer.normalize(article)
        first_pass_time = time.time() - start_time

        # Второй проход - работа с кэшем
        start_time = time.time()
        for article in articles:
            ArticleNormalizer.normalize(article)
        second_pass_time = time.time() - start_time

        # Второй проход должен быть быстрее
        self.assertLess(second_pass_time, first_pass_time * 0.5)

        # Проверяем что кэш заполнен
        cache_info = ArticleNormalizer.get_cache_info()
        self.assertEqual(cache_info['size'], len(articles))


class ArticleNormalizerEdgeCasesTestCase(TestCase):
    """Тесты граничных случаев"""

    def test_normalize_very_long_article(self):
        """Тест очень длинного артикула"""
        long_article = "A" * 1000 + "-" + "B" * 1000
        result = ArticleNormalizer.normalize(long_article)
        self.assertEqual(len(result), 2001)

    def test_normalize_unicode_characters(self):
        """Тест с Unicode символами"""
        # Кириллица
        self.assertEqual(ArticleNormalizer.normalize("АБВ-123"), "АБВ-123")

        # Китайские символы
        self.assertEqual(ArticleNormalizer.normalize("中文-123"), "中文-123")

    def test_normalize_multiple_consecutive_dashes(self):
        """Тест множественных последовательных тире"""
        self.assertEqual(ArticleNormalizer.normalize("A---B"), "A---B")
        self.assertEqual(ArticleNormalizer.normalize("A–—−B"), "A---B")

    def test_normalize_mixed_invisible_characters(self):
        """Тест смешанных невидимых символов"""
        article_with_invisibles = "N323\u200b\xa0\u2000-\u202f13W"
        result = ArticleNormalizer.normalize(article_with_invisibles)
        self.assertEqual(result, "N323-13W")
