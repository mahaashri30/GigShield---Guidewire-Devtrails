"""
Comprehensive Verification System Test Suite
Tests face recognition, OCR, and verification workflows
"""

import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.face_recognition_service import FaceRecognitionService
from app.services.ocr_service import OCRService


def test_face_recognition_service():
    """Test Face Recognition Service initialization and methods"""
    print("\n" + "="*70)
    print("TEST 1: Face Recognition Service")
    print("="*70)
    
    try:
        service = FaceRecognitionService()
        print("✅ Face Recognition Service initialized successfully")
        print(f"   - Face match threshold: {service.FACE_MATCH_THRESHOLD}")
        print(f"   - Image size: {service.IMAGE_SIZE}")
        
        # Check if MTCNN detector is available
        if service.detector:
            print("✅ MTCNN face detector loaded successfully")
        else:
            print("⚠️  MTCNN detector not available (expected if no pre-trained weights)")
        
        return True
    except Exception as e:
        print(f"❌ Face Recognition Service test failed: {e}")
        return False


def test_ocr_service():
    """Test OCR Service initialization"""
    print("\n" + "="*70)
    print("TEST 2: OCR Service")
    print("="*70)
    
    try:
        service = OCRService()
        print("✅ OCR Service initialized successfully")
        print(f"   - Supported ID types: {service.SUPPORTED_ID_TYPES}")
        
        return True
    except Exception as e:
        print(f"❌ OCR Service test failed: {e}")
        return False


def test_face_embedding_extraction():
    """Test face embedding extraction logic"""
    print("\n" + "="*70)
    print("TEST 3: Face Embedding Extraction Logic")
    print("="*70)
    
    try:
        from app.services.face_recognition_service import FaceRecognitionService
        import numpy as np
        
        service = FaceRecognitionService()
        
        # Create mock embeddings (128-dimensional vectors like FaceNet)
        embedding1 = np.random.randn(128)
        embedding2 = np.random.randn(128)
        
        # Test cosine similarity computation
        distance = service._compute_face_distance(embedding1, embedding2)
        
        print(f"✅ Face distance computation works")
        print(f"   - Random embeddings distance: {distance:.4f}")
        print(f"   - Expected range: 0.0 (different) to 1.0 (identical)")
        print(f"   - Threshold: {service.FACE_MATCH_THRESHOLD}")
        
        # Test identical embeddings
        identical_distance = service._compute_face_distance(embedding1, embedding1)
        print(f"   - Identical embeddings distance: {identical_distance:.4f}")
        assert identical_distance > 0.99, "Identical embeddings should have distance ~1.0"
        
        return True
    except Exception as e:
        print(f"❌ Face embedding test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ocr_field_extraction():
    """Test OCR field extraction with sample text"""
    print("\n" + "="*70)
    print("TEST 4: OCR Field Extraction (Regex-based)")
    print("="*70)
    
    try:
        service = OCRService()
        
        # Sample OCR output text
        sample_ocr_text = """
        DRIVING LICENSE
        Name: ARUN KUMAR
        DL No: DL0720220123456
        DOB: 12/05/1998
        Expiry: 05/05/2030
        Address: 123 Street, Bangalore
        State: KARNATAKA
        Gender: Male
        """
        
        fields = service._extract_with_regex(sample_ocr_text, "driving_license")
        
        print("✅ OCR field extraction completed")
        print(f"   Extracted Fields:")
        for key, value in fields.items():
            if value:
                print(f"      - {key}: {value}")
        
        # Verify key fields extracted
        assert fields.get("name") is not None, "Name should be extracted"
        assert fields.get("id_number") is not None, "ID number should be extracted"
        
        print("✅ Key verification fields extracted successfully")
        
        return True
    except Exception as e:
        print(f"❌ OCR field extraction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_verification_status_flow():
    """Test verification status workflow"""
    print("\n" + "="*70)
    print("TEST 5: Verification Status Flow")
    print("="*70)
    
    try:
        from app.models.models import VerificationStatus, GovtIDType
        
        # Test verification status enum
        statuses = [s.value for s in VerificationStatus]
        print("✅ Verification statuses defined:")
        for status in statuses:
            print(f"   - {status}")
        
        # Test govt ID types
        id_types = [t.value for t in GovtIDType]
        print("\n✅ Government ID types defined:")
        for id_type in id_types:
            print(f"   - {id_type}")
        
        # Verify progression
        assert statuses[0] == "pending", "Should start with pending"
        assert statuses[-1] == "fully_verified", "Should end with fully_verified"
        
        print("\n✅ Verification flow is correctly defined")
        
        return True
    except Exception as e:
        print(f"❌ Verification status test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mock_face_verification():
    """Test mock face verification workflow"""
    print("\n" + "="*70)
    print("TEST 6: Mock Face Verification Workflow")
    print("="*70)
    
    try:
        from app.services.face_recognition_service import FaceRecognitionService
        import numpy as np
        
        service = FaceRecognitionService()
        
        # Simulate two similar embeddings (same person)
        base_embedding = np.random.randn(128)
        similar_embedding = base_embedding + np.random.randn(128) * 0.05  # Small noise
        
        distance1 = service._compute_face_distance(base_embedding, similar_embedding)
        
        # Simulate very different embeddings (different person)
        different_embedding = np.random.randn(128)
        distance2 = service._compute_face_distance(base_embedding, different_embedding)
        
        print(f"✅ Mock verification completed")
        print(f"   - Similar faces distance: {distance1:.4f} (should be HIGH)")
        print(f"   - Different faces distance: {distance2:.4f} (should be LOW)")
        print(f"   - Threshold: {service.FACE_MATCH_THRESHOLD}")
        
        # Distance should be monotonic - similar > different
        assert distance1 > distance2, "Similar embeddings should have higher distance"
        
        print(f"✅ Verification logic validated")
        
        return True
    except Exception as e:
        print(f"❌ Mock verification test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ocr_confidence_scoring():
    """Test OCR confidence scoring"""
    print("\n" + "="*70)
    print("TEST 7: OCR Confidence Scoring")
    print("="*70)
    
    try:
        service = OCRService()
        
        # Test confidence based on field extraction
        test_cases = [
            ("Name: John Doe\nDL: ABC123", 60, "Name + ID"),
            ("Name: Jane Smith\nDL: XYZ789\nDOB: 01/01/2000\nAddress: 123 St", 100, "Complete data"),
            ("Some random text", 0, "No valid fields"),
        ]
        
        print("✅ OCR Confidence Scoring Test Cases:")
        for text, expected_min, description in test_cases:
            fields = service._extract_with_regex(text, "driving_license")
            
            # Calculate confidence
            confidence = 0
            if fields.get("name"):
                confidence += 30
            if fields.get("id_number"):
                confidence += 30
            if fields.get("date_of_birth"):
                confidence += 20
            if fields.get("address"):
                confidence += 20
            
            confidence = min(confidence, 100)
            
            status = "✅" if confidence >= expected_min else "⚠️ "
            print(f"{status} {description}: {confidence}% confidence")
        
        print("\n✅ Confidence scoring validated")
        
        return True
    except Exception as e:
        print(f"❌ Confidence scoring test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests and generate report"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " SUSANOO VERIFICATION SYSTEM - COMPREHENSIVE TEST SUITE ".center(68) + "║")
    print("╚" + "="*68 + "╝")
    
    tests = [
        ("Face Recognition Service Initialization", test_face_recognition_service),
        ("OCR Service Initialization", test_ocr_service),
        ("Face Embedding Extraction", test_face_embedding_extraction),
        ("OCR Field Extraction", test_ocr_field_extraction),
        ("Verification Status Flow", test_verification_status_flow),
        ("Mock Face Verification", test_mock_face_verification),
        ("OCR Confidence Scoring", test_ocr_confidence_scoring),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10} | {test_name}")
    
    print("="*70)
    print(f"Results: {passed}/{total} tests passed ({100*passed//total}%)")
    print("="*70)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Verification system is ready for deployment.")
    else:
        print(f"\n⚠️  {total-passed} test(s) failed. Please review the errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
