"""
Утилита для нормализации артикулов товаров.

Обеспечивает единообразное сравнение артикулов из разных источников
(МойСклад, Excel файлы, SimplePrint).
"""
import re
from typing import Dict, List, Optional
from functools import lru_cache


class ArticleNormalizer:
    """
    Класс для нормализации артикулов товаров.

    Нормализация включает:
    - Удаление лишних пробелов
    - Замену различных типов тире на стандартный дефис
    - Удаление невидимых символов
    - Приведение к единому формату

    Примеры:
        >>> normalizer = ArticleNormalizer()
        >>> normalizer.normalize("N323-13W ")
        "N323-13W"
        >>> normalizer.normalize("496–51850")  # em dash
        "496-51850"
        >>> normalizer.normalize("  n323-13w  ")
        "n323-13w"
    """

    # Паттерн для замены различных типов тире
    DASH_PATTERN = re.compile(r'[–—−‒]')

    # Паттерн для удаления невидимых символов
    INVISIBLE_PATTERN = re.compile(
        r'[\x00-\x1f\x7f-\x9f\xa0\u2000-\u200f\u2028-\u202f\u205f-\u206f]'
    )

    # Паттерн для удаления лишних пробелов
    SPACE_PATTERN = re.compile(r'\s+')

    @classmethod
    @lru_cache(maxsize=10000)
    def normalize(cls, article: Optional[str]) -> str:
        """
        Нормализует артикул для корректного сравнения.

        Args:
            article: Исходный артикул (может быть None)

        Returns:
            Нормализованный артикул в стандартном формате
            Пустая строка, если article is None или пустой

        Examples:
            >>> ArticleNormalizer.normalize("N323-13W ")
            "N323-13W"
            >>> ArticleNormalizer.normalize("496–51850")
            "496-51850"
            >>> ArticleNormalizer.normalize(None)
            ""
        """
        if not article:
            return ''

        # Конвертируем в строку и убираем пробелы по краям
        result = str(article).strip()

        # Заменяем различные виды тире на обычный дефис
        # Включает: en dash (–), em dash (—), minus (−), figure dash (‒)
        result = cls.DASH_PATTERN.sub('-', result)

        # Удаляем невидимые символы (кроме обычного пробела)
        result = cls.INVISIBLE_PATTERN.sub('', result)

        # Удаляем лишние пробелы внутри строки
        result = cls.SPACE_PATTERN.sub(' ', result).strip()

        return result

    @classmethod
    def normalize_batch(cls, articles: List[str]) -> Dict[str, str]:
        """
        Пакетная нормализация списка артикулов.

        Args:
            articles: Список исходных артикулов

        Returns:
            Словарь {исходный_артикул: нормализованный_артикул}

        Examples:
            >>> articles = ["N323-13W ", "496–51850", "  abc  "]
            >>> ArticleNormalizer.normalize_batch(articles)
            {"N323-13W ": "N323-13W", "496–51850": "496-51850", "  abc  ": "abc"}
        """
        return {article: cls.normalize(article) for article in articles}

    @classmethod
    def normalize_case_insensitive(cls, article: Optional[str]) -> str:
        """
        Нормализует артикул с приведением к нижнему регистру.

        Используется для регистронезависимого сравнения.

        Args:
            article: Исходный артикул

        Returns:
            Нормализованный артикул в нижнем регистре

        Examples:
            >>> ArticleNormalizer.normalize_case_insensitive("N323-13W")
            "n323-13w"
        """
        normalized = cls.normalize(article)
        return normalized.lower() if normalized else ''

    @classmethod
    def clear_cache(cls):
        """
        Очищает кэш нормализованных артикулов.

        Полезно для тестирования или при ограниченной памяти.
        """
        cls.normalize.cache_clear()

    @classmethod
    def get_cache_info(cls) -> dict:
        """
        Возвращает информацию о кэше.

        Returns:
            Словарь с информацией о кэше (hits, misses, size, maxsize)
        """
        cache_info = cls.normalize.cache_info()
        return {
            'hits': cache_info.hits,
            'misses': cache_info.misses,
            'size': cache_info.currsize,
            'maxsize': cache_info.maxsize
        }


# Вспомогательная функция для обратной совместимости
def normalize_article(article: Optional[str]) -> str:
    """
    Функция-обертка для быстрого доступа к нормализации.

    Args:
        article: Артикул для нормализации

    Returns:
        Нормализованный артикул

    Examples:
        >>> normalize_article("N323-13W ")
        "N323-13W"
    """
    return ArticleNormalizer.normalize(article)
