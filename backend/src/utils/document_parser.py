import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional
import pdfplumber
import logging

try:
    from docx import Document
except ImportError:
    Document = None

logger = logging.getLogger(__name__)


class DocumentParser:
    """Парсер для различных типов документов"""
    
    @staticmethod
    def parse_json(file_path: Path) -> Dict[str, Any]:
        """Парсинг JSON файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка парсинга JSON {file_path}: {e}")
            raise
    
    @staticmethod
    def parse_xml(file_path: Path) -> Dict[str, Any]:
        """Парсинг XML файла"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Простой парсинг XML в словарь
            result = {
                "root_tag": root.tag,
                "attributes": root.attrib,
                "text": root.text.strip() if root.text else "",
                "children": []
            }
            
            for child in root:
                child_data = {
                    "tag": child.tag,
                    "attributes": child.attrib,
                    "text": child.text.strip() if child.text else "",
                }
                result["children"].append(child_data)
            
            return result
        except Exception as e:
            logger.error(f"Ошибка парсинга XML {file_path}: {e}")
            raise
    
    @staticmethod
    def parse_pdf(file_path: Path) -> str:
        """Парсинг PDF файла"""
        try:
            text_parts = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"Ошибка парсинга PDF {file_path}: {e}")
            raise
    
    @staticmethod
    def parse_docx(file_path: Path) -> str:
        """Парсинг DOCX файла"""
        if Document is None:
            raise ImportError("python-docx не установлен. Установите: pip install python-docx")
        try:
            doc = Document(file_path)
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            return "\n\n".join(paragraphs)
        except Exception as e:
            logger.error(f"Ошибка парсинга DOCX {file_path}: {e}")
            raise
    
    @staticmethod
    def extract_text_from_json(json_data: Dict[str, Any]) -> str:
        """Извлечение текста из JSON структуры"""
        text_parts = []
        
        if isinstance(json_data, dict):
            # Обработка структуры с documents
            if "documents" in json_data:
                for doc in json_data["documents"]:
                    if "text_entities" in doc:
                        for entity in doc["text_entities"]:
                            if entity.get("type") == "plain" and entity.get("text"):
                                text_parts.append(entity["text"])
                    elif "text" in doc:
                        text_parts.append(doc["text"])
            else:
                # Рекурсивный обход
                for key, value in json_data.items():
                    if isinstance(value, str):
                        text_parts.append(value)
                    elif isinstance(value, (dict, list)):
                        text_parts.append(DocumentParser.extract_text_from_json(value))
        elif isinstance(json_data, list):
            for item in json_data:
                text_parts.append(DocumentParser.extract_text_from_json(item))
        
        return "\n\n".join(text_parts)
    
    @staticmethod
    def extract_text_from_xml(xml_data: Dict[str, Any]) -> str:
        """Извлечение текста из XML структуры"""
        text_parts = []
        
        if xml_data.get("text"):
            text_parts.append(xml_data["text"])
        
        for child in xml_data.get("children", []):
            if child.get("text"):
                text_parts.append(child["text"])
        
        return "\n\n".join(text_parts)
    
    @staticmethod
    def parse_document(file_path: Path) -> Dict[str, Any]:
        """Универсальный парсер документов"""
        suffix = file_path.suffix.lower()
        
        result = {
            "file_name": file_path.name,
            "file_path": str(file_path),
            "file_type": suffix[1:] if suffix else "unknown",
            "text": "",
            "metadata": {}
        }
        
        try:
            if suffix == ".json":
                json_data = DocumentParser.parse_json(file_path)
                result["text"] = DocumentParser.extract_text_from_json(json_data)
                result["metadata"]["json_data"] = json_data
            elif suffix == ".xml":
                xml_data = DocumentParser.parse_xml(file_path)
                result["text"] = DocumentParser.extract_text_from_xml(xml_data)
                result["metadata"]["xml_data"] = xml_data
            elif suffix == ".pdf":
                result["text"] = DocumentParser.parse_pdf(file_path)
            elif suffix in [".docx", ".doc"]:
                result["text"] = DocumentParser.parse_docx(file_path)
            else:
                # Попытка прочитать как текстовый файл
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    result["text"] = f.read()
            
            return result
        except Exception as e:
            logger.error(f"Ошибка парсинга документа {file_path}: {e}")
            result["error"] = str(e)
            return result

