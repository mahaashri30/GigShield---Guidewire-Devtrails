"""
OCR Service for Government ID scanning and data extraction.
Uses Tesseract OCR + optional AI for structured field extraction.
"""

import logging
from typing import Optional, Dict, Tuple
import io
import base64
import re
import httpx
from PIL import Image, ImageEnhance, ImageFilter
import json

logger = logging.getLogger(__name__)

try:
    import pytesseract
    from pytesseract import Output
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger.warning("Tesseract OCR not installed. Install: pip install pytesseract")
    logger.warning("Also install Tesseract-OCR: https://github.com/UB-Mannheim/tesseract/wiki")

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Google Generative AI not installed. Install: pip install google-generativeai")


class OCRService:
    """Handles optical character recognition for government ID documents."""
    
    SUPPORTED_ID_TYPES = ["driving_license", "voter_id", "aadhaar", "pan"]
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        """Initialize OCR service with optional Gemini API for structured extraction."""
        self.gemini_api_key = gemini_api_key
        if gemini_api_key and GEMINI_AVAILABLE:
            try:
                genai.configure(api_key=gemini_api_key)
                self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
                logger.info("Gemini API initialized for structured field extraction")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini API: {e}")
                self.gemini_model = None
        else:
            self.gemini_model = None
    
    @staticmethod
    def _download_image(image_url: str) -> Optional[Image.Image]:
        """Download image from URL."""
        try:
            with httpx.Client() as client:
                response = client.get(image_url, timeout=10.0)
                response.raise_for_status()
                return Image.open(io.BytesIO(response.content)).convert('RGB')
        except Exception as e:
            logger.error(f"Failed to download image: {e}")
            return None
    
    @staticmethod
    def _decode_base64_image(image_data: str) -> Optional[Image.Image]:
        """Decode base64 image string to PIL Image."""
        try:
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            return Image.open(io.BytesIO(image_bytes)).convert('RGB')
        except Exception as e:
            logger.error(f"Failed to decode base64 image: {e}")
            return None
    
    @staticmethod
    def _preprocess_image(image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR results:
        - Enhance contrast
        - Apply sharpening
        - Convert to grayscale
        - Denoise
        """
        try:
            # Enhance contrast (CLAHE-like)
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # Enhance brightness
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1.1)
            
            # Sharpen
            image = image.filter(ImageFilter.SHARPEN)
            
            # Denoise (median filter)
            image = image.filter(ImageFilter.MedianFilter(size=3))
            
            return image
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}")
            return image
    
    def extract_text_from_image(self, image: Image.Image) -> str:
        """Extract text from document image using Tesseract OCR."""
        try:
            if not OCR_AVAILABLE:
                logger.error("Tesseract OCR not available")
                return ""
            
            # Preprocess image
            processed = self._preprocess_image(image)
            
            # Extract text using Tesseract
            # Configure for better accuracy on document images
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(processed, config=custom_config, lang='eng')
            
            logger.debug(f"Extracted text length: {len(text)}")
            return text
        
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return ""
    
    def extract_structured_fields(
        self,
        text: str,
        id_type: str
    ) -> Dict[str, Optional[str]]:
        """
        Extract structured fields based on ID type using regex and optional Gemini.
        
        Returns: {
            "name": str,
            "id_number": str,
            "date_of_birth": str,
            "expiry_date": str,
            "address": str,
            ...
        }
        """
        try:
            # Try Gemini first if available
            if self.gemini_model:
                return self._extract_with_gemini(text, id_type)
            
            # Fallback to regex extraction
            return self._extract_with_regex(text, id_type)
        
        except Exception as e:
            logger.error(f"Field extraction failed: {e}")
            return {}
    
    def _extract_with_gemini(self, text: str, id_type: str) -> Dict[str, Optional[str]]:
        """Use Gemini to extract structured fields from OCR text."""
        try:
            if not self.gemini_model:
                return {}
            
            prompt = f"""
You are an expert at extracting information from government ID documents.

ID Type: {id_type}
OCR Text from document:
{text}

Extract the following fields as JSON:
- name: Full name of the person
- id_number: Document ID/Reference number
- date_of_birth: DOB in YYYY-MM-DD format (if available)
- expiry_date: Expiry/Validity date in YYYY-MM-DD format (if available)
- address: Address mentioned on ID (if available)
- gender: M/F (if available)
- state: State (for Indian documents)

Return ONLY valid JSON. If a field is not found, use null.
"""
            
            response = self.gemini_model.generate_content(prompt)
            
            # Parse JSON response
            try:
                fields = json.loads(response.text)
                logger.info(f"Gemini extraction successful: {fields}")
                return fields
            except json.JSONDecodeError:
                logger.warning("Gemini response was not valid JSON, falling back to regex")
                return self._extract_with_regex(text, id_type)
        
        except Exception as e:
            logger.error(f"Gemini extraction failed: {e}")
            return {}
    
    def _extract_with_regex(self, text: str, id_type: str) -> Dict[str, Optional[str]]:
        """Extract structured fields using regex patterns."""
        fields = {
            "name": None,
            "id_number": None,
            "date_of_birth": None,
            "expiry_date": None,
            "address": None,
            "gender": None,
            "state": None,
        }
        
        try:
            # Name extraction (usually first capitalized phrase)
            name_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', text)
            if name_match:
                fields["name"] = name_match.group(1)
            
            # Date patterns (DD/MM/YYYY, YYYY-MM-DD, DD-MM-YYYY)
            date_pattern = r'(\d{2}[-/]\d{2}[-/]\d{4}|\d{4}[-/]\d{2}[-/]\d{2})'
            dates = re.findall(date_pattern, text)
            
            if len(dates) >= 1:
                fields["date_of_birth"] = dates[0]
            if len(dates) >= 2:
                fields["expiry_date"] = dates[1]
            
            # ID number patterns (alphanumeric, usually 8-20 chars)
            id_pattern = r'[A-Z]{2}\d{7}|[A-Z0-9]{10,20}'
            id_match = re.search(id_pattern, text)
            if id_match:
                fields["id_number"] = id_match.group(0)
            
            # Gender extraction
            gender_match = re.search(r'\b(Male|Female|M|F)\b', text, re.IGNORECASE)
            if gender_match:
                fields["gender"] = gender_match.group(1)[0].upper()
            
            # State extraction (for Indian documents)
            states = [
                "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
                "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
                "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
                "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
                "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal"
            ]
            for state in states:
                if state.upper() in text.upper():
                    fields["state"] = state
                    break
            
            logger.info(f"Regex extraction complete: {fields}")
            return fields
        
        except Exception as e:
            logger.error(f"Regex extraction failed: {e}")
            return fields
    
    def verify_govt_id(
        self,
        id_image_data: str,
        id_type: str,
        is_base64: bool = True,
        verify_name: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Full government ID verification workflow.
        
        Args:
            id_image_data: Base64-encoded ID image or URL
            id_type: Type of ID (driving_license, voter_id, aadhaar, pan)
            is_base64: Whether id_image_data is base64 (True) or URL (False)
            verify_name: Optional name to verify against extracted name
        
        Returns:
            {
                "verified": bool,
                "extracted_fields": dict,
                "name_match": bool (if verify_name provided),
                "confidence": float,  # 0-100% confidence in extraction
                "error": Optional[str]
            }
        """
        try:
            # Load and preprocess image
            id_image = (
                self._decode_base64_image(id_image_data)
                if is_base64
                else self._download_image(id_image_data)
            )
            
            if id_image is None:
                return {
                    "verified": False,
                    "extracted_fields": {},
                    "name_match": False,
                    "confidence": 0.0,
                    "error": "Failed to load government ID image"
                }
            
            # Extract text via OCR
            extracted_text = self.extract_text_from_image(id_image)
            
            if not extracted_text or len(extracted_text.strip()) < 20:
                return {
                    "verified": False,
                    "extracted_fields": {},
                    "name_match": False,
                    "confidence": 0.0,
                    "error": "Could not extract sufficient text from ID image"
                }
            
            # Extract structured fields
            fields = self.extract_structured_fields(extracted_text, id_type)
            
            # Verify extracted data
            has_name = bool(fields.get("name"))
            has_id = bool(fields.get("id_number"))
            
            # Optional name verification
            name_match = False
            if verify_name and fields.get("name"):
                # Simple name matching (check if last names match)
                extracted_name = fields.get("name", "").lower()
                verify_name_lower = verify_name.lower()
                name_parts = extracted_name.split()
                verify_parts = verify_name_lower.split()
                
                # Check if any significant name part matches
                name_match = any(
                    part in verify_parts
                    for part in name_parts
                    if len(part) > 3
                )
            
            # Confidence based on field extraction
            field_confidence = 0.0
            if has_name:
                field_confidence += 30
            if has_id:
                field_confidence += 30
            if fields.get("date_of_birth"):
                field_confidence += 20
            if fields.get("address"):
                field_confidence += 20
            
            verified = has_name and has_id
            
            logger.info(
                f"Govt ID verification: type={id_type}, verified={verified}, "
                f"confidence={field_confidence}, name_match={name_match}"
            )
            
            return {
                "verified": verified,
                "extracted_fields": fields,
                "name_match": name_match if verify_name else None,
                "confidence": min(field_confidence, 100.0),
                "error": None
            }
        
        except Exception as e:
            logger.error(f"Government ID verification failed: {e}", exc_info=True)
            return {
                "verified": False,
                "extracted_fields": {},
                "name_match": False,
                "confidence": 0.0,
                "error": f"ID verification error: {str(e)}"
            }
