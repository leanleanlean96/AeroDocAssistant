"""Скрипт для инициализации базы данных примерами документов"""
import asyncio
import json
import sys
from pathlib import Path

# Добавить src в путь
sys.path.insert(0, str(Path(__file__).parent / "src"))

from backend.src.config import settings
from backend.src.database.vector_db import VectorDatabase
from backend.src.services.embeddings_service import SberEmbeddingsService
from backend.src.services.document_service import DocumentService
from backend.src.models.schemas import DocumentCreate, DocumentType


# Примеры документов для инициализации
SAMPLE_DOCUMENTS = [
    {
        "title": "Чертеж крыла МС-21",
        "content": "Основной чертеж конструкции крыла с указанием всех размеров, материалов и допусков. Крыло изготавливается из алюминиевого сплава АМГ6М в соответствии с ГОСТ 4784. Толщина обшивки 1,5 мм. Требуется применение клепки типа 'холодная' по ГОСТ 14162-79. Допуск на размеры ±0,5 мм. Поверхность должна быть обработана в соответствии с требованиями эмиссионности.",
        "document_type": DocumentType.ESKD,
        "doc_number": "МС-21-WG-001",
        "version": "3.2",
        "author": "Конструкторский отдел МАЗ",
        "tags": ["wing", "structural", "MS-21", "aluminum"]
    },
    {
        "title": "Технологический процесс сборки фюзеляжа",
        "content": "Процесс включает следующие операции: 1) Подготовка деталей (очистка, осмотр). 2) Предварительная сборка (совмещение и фиксация). 3) Клепка по утвержденной схеме. 4) Герметизация швов. 5) Контроль качества. Время цикла сборки: 8 часов. Требуемый квалификационный уровень персонала: 3-4 разряд.",
        "document_type": DocumentType.ESTD,
        "doc_number": "МС-21-TP-024",
        "version": "2.1",
        "author": "Технологический отдел",
        "tags": ["assembly", "fuselage", "production"]
    },
    {
        "title": "Руководство по ремонту радиатора охлаждения",
        "content": "При выявлении утечек теплоносителя необходимо: 1. Слить охлаждающую жидкость (объем 15 л). 2. Снять радиатор с кронштейнов. 3. Провести гидравлическое испытание при давлении 1.5 МПа. 4. При обнаружении дефектов - замена на новый узел. 5. Заполнить систему новой охлаждающей жидкостью, прокачать воздух.",
        "document_type": DocumentType.REPAIR_MANUAL,
        "doc_number": "МС-21-RM-156",
        "version": "1.0",
        "author": "Служба технического обслуживания",
        "tags": ["maintenance", "cooling_system", "repair"]
    },
    {
        "title": "Сертификат сплава АМГ6М",
        "content": "Алюминиевый деформируемый сплав АМГ6М соответствует ГОСТ 4784-97. Содержание магния 5-6.8%, марганца 0.5-1.0%, меди не более 0.1%, циркония не более 0.15%. Предел прочности: 310 МПа, предел текучести: 160 МПа, относительное удлинение: 12-15%. Плотность: 2700 кг/м3. Температура плавления: 650°C.",
        "document_type": DocumentType.MATERIAL_CERT,
        "doc_number": "ГОСТ 4784-97",
        "version": "1.0",
        "author": "ВАМИ (Всероссийский алюминиево-магниевый институт)",
        "tags": ["aluminum", "alloy", "material", "certification"]
    },
    {
        "title": "Отчет о прочностных испытаниях крыла",
        "content": "Испытания проведены согласно программе CS-23.561. Максимальная расчетная нагрузка: 6.5g. При нагружении образец выдержал нагрузку без видимых повреждений. Опасные значения напряжения не обнаружены. Коэффициент безопасности: 1.5. Рекомендация: одобрить конструкцию к серийному производству. Дата испытания: 15 ноября 2023 г.",
        "document_type": DocumentType.TEST_REPORT,
        "doc_number": "МС-21-TR-089",
        "version": "1.0",
        "author": "Испытательная лаборатория",
        "tags": ["testing", "strength", "certification", "wing"]
    },
    {
        "title": "ГОСТ Р 57453-2021 Самолеты гражданские. Требования авиационной безопасности",
        "content": "Настоящий стандарт устанавливает требования авиационной безопасности к самолетам гражданской авиации. Включает требования к конструкции, системам управления, систем питания, систем авиационной электрооборудования, эксплуатационным ограничениям. Применяется ко всем самолетам, сертифицируемым в Российской Федерации.",
        "document_type": DocumentType.STANDARD,
        "doc_number": "ГОСТ Р 57453-2021",
        "version": "1.0",
        "author": "Межгосударственная система по стандартизации",
        "tags": ["standard", "safety", "regulation", "certification"]
    },
]


async def init_sample_documents():
    """Инициализировать БД примерами документов"""
    try:
        print("Инициализация примеров документов...")
        
        # Инициализировать сервисы
        vector_db = VectorDatabase(settings.chroma_db_path)
        embeddings_service = SberEmbeddingsService(
            api_key=settings.sber_api_key,
            api_url=settings.sber_api_url
        )
        doc_service = DocumentService(vector_db, embeddings_service)
        
        # Добавить документы
        for i, doc_data in enumerate(SAMPLE_DOCUMENTS):
            print(f"\nДобавление документа {i+1}/{len(SAMPLE_DOCUMENTS)}: {doc_data['title']}")
            
            doc_create = DocumentCreate(**doc_data)
            await doc_service.create_document(doc_create)
            
            print(f"✓ Документ добавлен")
        
        # Получить статистику
        stats = doc_service.get_statistics()
        print(f"\n✓ Инициализация завершена!")
        print(f"Всего документов: {stats.get('total_documents', 0)}")
        print(f"Статистика по типам: {stats.get('documents_by_type', {})}")
        
        await embeddings_service.close()
        
    except Exception as e:
        print(f"✗ Ошибка при инициализации: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(init_sample_documents())
