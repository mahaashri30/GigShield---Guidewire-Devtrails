"""
AWS Bedrock AI Service for Face Recognition and OCR
Uses Claude Vision and multimodal models for biometric verification
"""

import json
import base64
import logging
from typing import Optional, Dict, Any
from io import BytesIO

import boto3
from botocore.exceptions import ClientError
from PIL import Image

logger = logging.getLogger(__name__)


class BedrockAIService:
    """AWS Bedrock service for AI/ML operations"""

    def __init__(self, region_name: str = "us-east-1"):
        """
        Initialize Bedrock client
        
        Args:
            region_name: AWS region (default: us-east-1)
            
        Required AWS Credentials:
            - AWS_ACCESS_KEY_ID
            - AWS_SECRET_ACCESS_KEY
            - Or IAM role with bedrock:InvokeModel permissions
        """
        try:
            self.bedrock_runtime = boto3.client(
                "bedrock-runtime",
                region_name=region_name
            )
            self.s3_client = boto3.client(
                "s3",
                region_name=region_name
            )
            logger.info(f"✓ Bedrock client initialized for region: {region_name}")
        except Exception as e:
            logger.error(f"✗ Failed to initialize Bedrock client: {e}")
            raise

    def verify_selfie_with_id(
        self,
        selfie_image_data: bytes,
        id_image_data: bytes,
        is_base64: bool = False
    ) -> Dict[str, Any]:
        """
        Compare selfie against government ID using Claude Vision
        
        Args:
            selfie_image_data: Selfie image (bytes or base64)
            id_image_data: Government ID image (bytes or base64)
            is_base64: Whether images are base64 encoded
            
        Returns:
            {
                "verified": bool,
                "match_score": float (0-1),
                "confidence": float (0-100),
                "face_quality": str,
                "liveness_score": float,
                "error": Optional[str]
            }
        """
        try:
            # Decode if base64
            if is_base64:
                selfie_bytes = base64.b64decode(selfie_image_data)
                id_bytes = base64.b64decode(id_image_data)
            else:
                selfie_bytes = selfie_image_data
                id_bytes = id_image_data

            # Convert to base64 for Bedrock API
            selfie_b64 = base64.b64encode(selfie_bytes).decode("utf-8")
            id_b64 = base64.b64encode(id_bytes).decode("utf-8")

            # Invoke Claude Vision model
            prompt = """Analyze these two images:
1. First image: A selfie (face photo)
2. Second image: A government ID document

Please provide:
1. Are these the SAME PERSON? (yes/no)
2. Confidence score (0-100): How confident are you?
3. Face quality (excellent/good/fair/poor)
4. Liveness indicators (is the selfie of a real person, not a photo?)
5. Any facial features that match/don't match

Respond in JSON format:
{
    "same_person": boolean,
    "confidence": number 0-100,
    "face_quality": string,
    "liveness_detected": boolean,
    "matching_features": [list],
    "mismatches": [list],
    "notes": string
}"""

            message = self.bedrock_runtime.invoke_model(
                modelId="anthropic.claude-3-5-sonnet-20241022",
                contentType="application/json",
                accept="application/json",
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-06-01",
                    "max_tokens": 1024,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/jpeg",
                                        "data": selfie_b64
                                    }
                                },
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/jpeg",
                                        "data": id_b64
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": prompt
                                }
                            ]
                        }
                    ]
                })
            )

            # Parse response
            response_body = json.loads(message["body"].read())
            response_text = response_body["content"][0]["text"]

            # Extract JSON from response
            try:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                json_str = response_text[json_start:json_end]
                analysis = json.loads(json_str)
            except (ValueError, IndexError):
                logger.warning(f"Could not parse JSON from response: {response_text}")
                analysis = {
                    "same_person": False,
                    "confidence": 0,
                    "face_quality": "unknown",
                    "liveness_detected": False
                }

            # Calculate match score (0-1 range)
            match_score = min(analysis.get("confidence", 0) / 100.0, 1.0)
            
            # Determine if verified (confidence > 75% and liveness detected)
            is_verified = (
                analysis.get("same_person", False) and
                analysis.get("confidence", 0) > 75 and
                analysis.get("liveness_detected", True)
            )

            return {
                "verified": is_verified,
                "match_score": round(match_score, 4),
                "confidence": round(analysis.get("confidence", 0), 2),
                "face_quality": analysis.get("face_quality", "unknown"),
                "liveness_score": 0.95 if analysis.get("liveness_detected") else 0.1,
                "error": None
            }

        except ClientError as e:
            error_msg = f"Bedrock API error: {e.response['Error']['Message']}"
            logger.error(error_msg)
            return {
                "verified": False,
                "match_score": 0.0,
                "confidence": 0.0,
                "face_quality": "error",
                "liveness_score": 0.0,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"Face verification error: {str(e)}"
            logger.error(error_msg)
            return {
                "verified": False,
                "match_score": 0.0,
                "confidence": 0.0,
                "face_quality": "error",
                "liveness_score": 0.0,
                "error": error_msg
            }

    def extract_govt_id_fields(
        self,
        id_image_data: bytes,
        id_type: str,
        is_base64: bool = False
    ) -> Dict[str, Any]:
        """
        Extract fields from government ID using Claude Vision + OCR
        
        Args:
            id_image_data: Government ID image (bytes or base64)
            id_type: Type of ID (DRIVING_LICENSE, VOTER_ID, AADHAAR, PAN)
            is_base64: Whether image is base64 encoded
            
        Returns:
            {
                "extracted_fields": {
                    "name": str,
                    "id_number": str,
                    "date_of_birth": str,
                    "expiry_date": str,
                    "address": str,
                    "gender": str,
                    "state": str
                },
                "confidence": float (0-100),
                "quality_score": float (0-100),
                "error": Optional[str]
            }
        """
        try:
            # Decode if base64
            if is_base64:
                image_bytes = base64.b64decode(id_image_data)
            else:
                image_bytes = id_image_data

            # Convert to base64 for Bedrock API
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")

            # Create prompt based on ID type
            if id_type == "DRIVING_LICENSE":
                fields_desc = "name, license number, date of birth, expiry date, license class, address"
            elif id_type == "VOTER_ID":
                fields_desc = "voter name, voter ID number, state, constituency"
            elif id_type == "AADHAAR":
                fields_desc = "name, Aadhaar number, date of birth, gender, address"
            elif id_type == "PAN":
                fields_desc = "name, PAN number, date of birth, father's name"
            else:
                fields_desc = "name, ID number, date of birth, expiry date, address"

            prompt = f"""Analyze this {id_type} document image and extract all readable information.

Extract the following fields: {fields_desc}

Important:
- Be precise with dates (format as YYYY-MM-DD)
- Extract exactly as shown on the document
- If a field is not visible or unclear, set to null
- Provide a quality_score (0-100) indicating document clarity
- Provide a confidence_score (0-100) indicating extraction certainty

Respond in JSON format:
{{
    "name": string or null,
    "id_number": string or null,
    "date_of_birth": string or null,
    "expiry_date": string or null,
    "address": string or null,
    "gender": string or null,
    "state": string or null,
    "quality_score": number 0-100,
    "confidence_score": number 0-100,
    "notes": string
}}"""

            message = self.bedrock_runtime.invoke_model(
                modelId="anthropic.claude-3-5-sonnet-20241022",
                contentType="application/json",
                accept="application/json",
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-06-01",
                    "max_tokens": 1024,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/jpeg",
                                        "data": image_b64
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": prompt
                                }
                            ]
                        }
                    ]
                })
            )

            # Parse response
            response_body = json.loads(message["body"].read())
            response_text = response_body["content"][0]["text"]

            # Extract JSON from response
            try:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                json_str = response_text[json_start:json_end]
                extraction = json.loads(json_str)
            except (ValueError, IndexError):
                logger.warning(f"Could not parse JSON from response: {response_text}")
                extraction = {
                    "name": None,
                    "id_number": None,
                    "date_of_birth": None,
                    "quality_score": 0,
                    "confidence_score": 0
                }

            return {
                "extracted_fields": {
                    "name": extraction.get("name"),
                    "id_number": extraction.get("id_number"),
                    "date_of_birth": extraction.get("date_of_birth"),
                    "expiry_date": extraction.get("expiry_date"),
                    "address": extraction.get("address"),
                    "gender": extraction.get("gender"),
                    "state": extraction.get("state")
                },
                "confidence": round(extraction.get("confidence_score", 0), 2),
                "quality_score": round(extraction.get("quality_score", 0), 2),
                "error": None
            }

        except ClientError as e:
            error_msg = f"Bedrock API error: {e.response['Error']['Message']}"
            logger.error(error_msg)
            return {
                "extracted_fields": {},
                "confidence": 0.0,
                "quality_score": 0.0,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"OCR extraction error: {str(e)}"
            logger.error(error_msg)
            return {
                "extracted_fields": {},
                "confidence": 0.0,
                "quality_score": 0.0,
                "error": error_msg
            }

    async def verify_govt_id(
        self,
        id_image_data: bytes,
        id_type: str,
        is_base64: bool = False,
        verify_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Complete government ID verification with field extraction and validation
        
        Args:
            id_image_data: Government ID image
            id_type: Type of ID document
            is_base64: Whether image is base64
            verify_name: Optional name to verify against extraction
            
        Returns:
            {
                "verified": bool,
                "extracted_fields": dict,
                "name_match": bool,
                "confidence": float,
                "error": Optional[str]
            }
        """
        # Extract fields
        extraction = self.extract_govt_id_fields(id_image_data, id_type, is_base64)
        
        if extraction["error"]:
            return {
                "verified": False,
                "extracted_fields": {},
                "name_match": False,
                "confidence": 0.0,
                "error": extraction["error"]
            }

        extracted_name = extraction["extracted_fields"].get("name", "").strip().lower()
        name_match = False
        
        if verify_name:
            verify_name_lower = verify_name.strip().lower()
            # Check if names match (allowing for partial matches)
            name_match = (
                extracted_name == verify_name_lower or
                extracted_name in verify_name_lower or
                verify_name_lower in extracted_name
            )

        # Determine if verification passed
        is_verified = (
            extraction["confidence"] > 75 and
            extraction["quality_score"] > 60 and
            (name_match if verify_name else True)
        )

        return {
            "verified": is_verified,
            "extracted_fields": extraction["extracted_fields"],
            "name_match": name_match if verify_name else None,
            "confidence": extraction["confidence"],
            "error": None
        }
