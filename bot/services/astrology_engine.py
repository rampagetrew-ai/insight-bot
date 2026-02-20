"""Астрологический движок — расчёт натальных карт и транзитов."""

from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

# Пытаемся импортировать flatlib, если доступен
try:
    from flatlib import const
    from flatlib.chart import Chart
    from flatlib.datetime import Datetime as FlatDateTime
    from flatlib.geopos import GeoPos
    from flatlib.aspect import Aspect
    FLATLIB_AVAILABLE = True
except ImportError:
    FLATLIB_AVAILABLE = False


@dataclass
class PlanetPosition:
    """Позиция планеты в карте."""
    name: str
    sign: str
    degree: float
    house: int
    retrograde: bool = False
    
    @property
    def sign_emoji(self) -> str:
        """Возвращает эмодзи знака."""
        SIGNS = {
            "Aries": "♈", "Taurus": "♉", "Gemini": "♊",
            "Cancer": "♋", "Leo": "♌", "Virgo": "♍",
            "Libra": "♎", "Scorpio": "♏", "Sagittarius": "♐",
            "Capricorn": "♑", "Aquarius": "♒", "Pisces": "♓",
        }
        return SIGNS.get(self.sign, "")
    
    @property
    def display(self) -> str:
        """Форматированное отображение."""
        retro = " ℞" if self.retrograde else ""
        return f"{self.sign_emoji} {self.sign} {self.degree:.1f}°{retro} (дом {self.house})"


@dataclass
class NatalChart:
    """Натальная карта."""
    sun: PlanetPosition
    moon: PlanetPosition
    ascendant: PlanetPosition
    mercury: Optional[PlanetPosition] = None
    venus: Optional[PlanetPosition] = None
    mars: Optional[PlanetPosition] = None
    jupiter: Optional[PlanetPosition] = None
    saturn: Optional[PlanetPosition] = None
    uranus: Optional[PlanetPosition] = None
    neptune: Optional[PlanetPosition] = None
    pluto: Optional[PlanetPosition] = None
    
    def get_triad(self) -> Dict[str, PlanetPosition]:
        """Возвращает триаду: Солнце, Луна, Асцендент."""
        return {
            "sun": self.sun,
            "moon": self.moon,
            "ascendant": self.ascendant,
        }


class AstrologyEngine:
    """Движок астрологических расчётов."""
    
    # Знаки зодиака
    SIGNS = [
        "Aries", "Taurus", "Gemini", "Cancer",
        "Leo", "Virgo", "Libra", "Scorpio",
        "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    
    SIGN_EMOJIS = {
        "Aries": "♈", "Taurus": "♉", "Gemini": "♊",
        "Cancer": "♋", "Leo": "♌", "Virgo": "♍",
        "Libra": "♎", "Scorpio": "♏", "Sagittarius": "♐",
        "Capricorn": "♑", "Aquarius": "♒", "Pisces": "♓",
    }
    
    # Планеты
    PLANETS = {
        "Sun": "☉ Солнце",
        "Moon": "☽ Луна",
        "Mercury": "☿ Меркурий",
        "Venus": "♀ Венера",
        "Mars": "♂ Марс",
        "Jupiter": "♃ Юпитер",
        "Saturn": "♄ Сатурн",
        "Uranus": "♅ Уран",
        "Neptune": "♆ Нептун",
        "Pluto": "♇ Плутон",
    }
    
    # Элементы знаков
    SIGN_ELEMENTS = {
        "Aries": "Огонь", "Leo": "Огонь", "Sagittarius": "Огонь",
        "Taurus": "Земля", "Virgo": "Земля", "Capricorn": "Земля",
        "Gemini": "Воздух", "Libra": "Воздух", "Aquarius": "Воздух",
        "Cancer": "Вода", "Scorpio": "Вода", "Pisces": "Вода",
    }
    
    # Качества знаков
    SIGN_QUALITIES = {
        "Aries": "Кардинальный", "Cancer": "Кардинальный",
        "Libra": "Кардинальный", "Capricorn": "Кардинальный",
        "Taurus": "Фиксированный", "Leo": "Фиксированный",
        "Scorpio": "Фиксированный", "Aquarius": "Фиксированный",
        "Gemini": "Мутабельный", "Virgo": "Мутабельный",
        "Sagittarius": "Мутабельный", "Pisces": "Мутабельный",
    }
    
    def __init__(self):
        self.flatlib_available = FLATLIB_AVAILABLE
    
    def calculate_natal_chart(
        self,
        birth_date: datetime,
        birth_time: Optional[str],
        latitude: float,
        longitude: float,
    ) -> Optional[NatalChart]:
        """Рассчитывает натальную карту."""
        
        if not self.flatlib_available:
            # Fallback: примерный расчёт по дате
            return self._approximate_chart(birth_date, latitude, longitude)
        
        try:
            # Парсим время
            if birth_time:
                hour, minute = map(int, birth_time.split(":"))
            else:
                hour, minute = 12, 0  # Полдень по умолчанию
            
            # Создаём объект datetime для flatlib
            dt = FlatDateTime(
                birth_date.year,
                birth_date.month,
                birth_date.day,
                hour,
                minute,
            )
            
            # Геопозиция
            pos = GeoPos(latitude, longitude)
            
            # Строим карту
            chart = Chart(dt, pos)
            
            # Извлекаем планеты
            sun = self._get_planet_position(chart, const.SUN, "Sun")
            moon = self._get_planet_position(chart, const.MOON, "Moon")
            asc = self._get_ascendant(chart)
            
            return NatalChart(
                sun=sun,
                moon=moon,
                ascendant=asc,
                mercury=self._get_planet_position(chart, const.MERCURY, "Mercury"),
                venus=self._get_planet_position(chart, const.VENUS, "Venus"),
                mars=self._get_planet_position(chart, const.MARS, "Mars"),
                jupiter=self._get_planet_position(chart, const.JUPITER, "Jupiter"),
                saturn=self._get_planet_position(chart, const.SATURN, "Saturn"),
                uranus=self._get_planet_position(chart, const.URANUS, "Uranus"),
                neptune=self._get_planet_position(chart, const.NEPTUNE, "Neptune"),
                pluto=self._get_planet_position(chart, const.PLUTO, "Pluto"),
            )
            
        except Exception as e:
            print(f"Error calculating chart: {e}")
            return self._approximate_chart(birth_date, latitude, longitude)
    
    def _get_planet_position(self, chart, planet_const, name: str) -> Optional[PlanetPosition]:
        """Извлекает позицию планеты из карты."""
        try:
            planet = chart.get(planet_const)
            return PlanetPosition(
                name=name,
                sign=planet.sign,
                degree=planet.lon,
                house=self._get_house(planet.house),
                retrograde=planet.retrograde,
            )
        except:
            return None
    
    def _get_ascendant(self, chart) -> PlanetPosition:
        """Извлекает асцендент."""
        asc = chart.get(const.ASC)
        return PlanetPosition(
            name="Ascendant",
            sign=asc.sign,
            degree=asc.lon,
            house=1,
            retrograde=False,
        )
    
    def _get_house(self, house_obj) -> int:
        """Получает номер дома."""
        try:
            return int(house_obj.id)
        except:
            return 1
    
    def _approximate_chart(
        self,
        birth_date: datetime,
        latitude: float,
        longitude: float,
    ) -> NatalChart:
        """Приблизительный расчёт без flatlib (fallback)."""
        # Упрощённый расчёт — для демо
        day_of_year = birth_date.timetuple().tm_yday
        
        # Солнце: ~1 градус в день
        sun_sign_idx = (day_of_year // 30) % 12
        sun_degree = day_of_year % 30
        
        # Луна: ~13 градусов в день
        moon_offset = (day_of_year * 13) % 360
        moon_sign_idx = int(moon_offset // 30)
        moon_degree = moon_offset % 30
        
        # Асцендент: упрощённо по времени
        hour = birth_date.hour if birth_date.hour else 12
        asc_offset = (hour * 15 + longitude / 2) % 360
        asc_sign_idx = int(asc_offset // 30)
        asc_degree = asc_offset % 30
        
        return NatalChart(
            sun=PlanetPosition("Sun", self.SIGNS[sun_sign_idx], sun_degree, 5),
            moon=PlanetPosition("Moon", self.SIGNS[moon_sign_idx], moon_degree, 4),
            ascendant=PlanetPosition("Ascendant", self.SIGNS[asc_sign_idx], asc_degree, 1),
        )
    
    def get_sign_meaning(self, planet: str, sign: str) -> str:
        """Возвращает значение планеты в знаке."""
        meanings = {
            ("Sun", "Aries"): "Лидерство, импульсивность, необходимость действовать первым",
            ("Sun", "Taurus"): "Стабильность, упорство, ценность комфорта и красоты",
            ("Sun", "Gemini"): "Любознательность, многозадачность, коммуникабельность",
            ("Sun", "Cancer"): "Эмоциональная глубина, забота о близких, привязанность к дому",
            ("Sun", "Leo"): "Творчество, самовыражение, необходимость признания",
            ("Sun", "Virgo"): "Аналитичность, стремление к совершенству, полезность",
            ("Sun", "Libra"): "Гармония, партнёрство, чувство справедливости",
            ("Sun", "Scorpio"): "Глубина трансформации, интенсивность, магнетизм",
            ("Sun", "Sagittarius"): "Философия, свобода, поиск смысла и приключений",
            ("Sun", "Capricorn"): "Амбиции, дисциплина, строительство долгосрочного",
            ("Sun", "Aquarius"): "Оригинальность, гуманизм, независимость",
            ("Sun", "Pisces"): "Эмпатия, интуиция, размывание границ",
            
            ("Moon", "Aries"): "Эмоции вспыхивают быстро, нужда в немедленной реакции",
            ("Moon", "Taurus"): "Эмоциональная стабильность, утешение в материальном",
            ("Moon", "Gemini"): "Эмоции через общение, переменчивость настроения",
            ("Moon", "Cancer"): "Глубокая эмоциональная чувствительность, забота",
            ("Moon", "Leo"): "Эмоциональная щедрость, нужда в восхищении",
            ("Moon", "Virgo"): "Эмоции через служение, беспокойство о деталях",
            ("Moon", "Libra"): "Эмоциональная зависимость от гармонии в отношениях",
            ("Moon", "Scorpio"): "Интенсивные эмоции, страх предательства",
            ("Moon", "Sagittarius"): "Эмоции через свободу и философию",
            ("Moon", "Capricorn"): "Сдержанность эмоций, ответственность за других",
            ("Moon", "Aquarius"): "Эмоциональная отстранённость, забота о коллективе",
            ("Moon", "Pisces"): "Поглощение чужих эмоций, эмпатия без границ",
        }
        
        return meanings.get((planet, sign), f"{planet} в {sign}: уникальное проявление энергии")
    
    def get_triad_interpretation(self, chart: NatalChart) -> Dict[str, str]:
        """Интерпретирует триаду Солнце-Луна-Асцендент."""
        triad = chart.get_triad()
        
        interpretations = {}
        
        # Солнце — суть
        sun = triad["sun"]
        interpretations["sun"] = {
            "title": "☉ Солнце — Твоя суть",
            "sign": sun.sign,
            "emoji": self.SIGN_EMOJIS.get(sun.sign, ""),
            "element": self.SIGN_ELEMENTS.get(sun.sign, ""),
            "meaning": self.get_sign_meaning("Sun", sun.sign),
            "house": f"Дом {sun.house} — сфера самовыражения",
        }
        
        # Луна — эмоции
        moon = triad["moon"]
        interpretations["moon"] = {
            "title": "☽ Луна — Твои эмоции",
            "sign": moon.sign,
            "emoji": self.SIGN_EMOJIS.get(moon.sign, ""),
            "element": self.SIGN_ELEMENTS.get(moon.sign, ""),
            "meaning": self.get_sign_meaning("Moon", moon.sign),
            "house": f"Дом {moon.house} — сфера эмоционального комфорта",
        }
        
        # Асцендент — маска
        asc = triad["ascendant"]
        interpretations["ascendant"] = {
            "title": "↑ Асцендент — Твоя маска",
            "sign": asc.sign,
            "emoji": self.SIGN_EMOJIS.get(asc.sign, ""),
            "element": self.SIGN_ELEMENTS.get(asc.sign, ""),
            "meaning": f"Как тебя видят другие при первой встрече. {self.SIGN_QUALITIES.get(asc.sign, '')} подход к жизни.",
            "house": "1 дом — личность и тело",
        }
        
        # Синтез
        interpretations["synthesis"] = self._synthesize_triad(
            sun.sign, moon.sign, asc.sign
        )
        
        return interpretations
    
    def _synthesize_triad(self, sun: str, moon: str, asc: str) -> str:
        """Создаёт синтез триады."""
        elements = {
            self.SIGN_ELEMENTS.get(sun, ""),
            self.SIGN_ELEMENTS.get(moon, ""),
            self.SIGN_ELEMENTS.get(asc, ""),
        }
        
        if len(elements) == 1:
            return f"Триада в элементе {list(elements)[0]}: концентрированная энергия, ярко выраженные качества"
        elif len(elements) == 2:
            return f"Два элемента ({' + '.join(elements)}): баланс между противоположностями"
        else:
            return f"Три элемента: разносторонняя личность, множество талантов"
    
    def calculate_transits(
        self,
        natal_chart: NatalChart,
        date: Optional[datetime] = None,
    ) -> List[Dict]:
        """Рассчитывает транзиты на дату."""
        if date is None:
            date = datetime.now()
        
        # Упрощённый расчёт — для MVP
        transits = []
        
        # Солнце: 1 градус в день
        day_of_year = date.timetuple().tm_yday
        sun_sign = self.SIGNS[(day_of_year // 30) % 12]
        
        # Проверяем конъюнкции с натальными планетами
        natal_sun = natal_chart.sun.sign
        if sun_sign == natal_sun:
            transits.append({
                "planet": "Sun",
                "aspect": "conjunction",
                "natal_planet": "Sun",
                "meaning": "☉ Солнце возвращается — время нового цикла, пересмотра целей",
                "intensity": "high",
            })
        
        # Луна: меняется каждые 2-3 дня
        moon_sign_idx = (day_of_year * 13 // 30) % 12
        moon_sign = self.SIGNS[moon_sign_idx]
        
        transits.append({
            "planet": "Moon",
            "sign": moon_sign,
            "meaning": f"☽ Луна в {moon_sign}: эмоциональный фон дня",
            "intensity": "daily",
        })
        
        return transits


# Глобальный экземпляр
astrology = AstrologyEngine()
