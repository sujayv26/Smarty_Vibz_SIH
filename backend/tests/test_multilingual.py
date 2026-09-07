import pytest
import json
from app.services.mock_provider import MockExtractionProvider
from app.schemas.progress import ProgressEventCreate, EventType
from app.schemas.agent import UnderstoodProgress

# Load benchmark fixture
import os
fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "multilingual_benchmark.json")
with open(fixture_path, "r") as f:
    BENCHMARK = json.load(f)

BENCHMARK_CASES = BENCHMARK["benchmark_cases"]
ACCURACY_THRESHOLD = BENCHMARK["accuracy_threshold"]


class TestMultilingualExtraction:
    @pytest.fixture
    def provider(self):
        return MockExtractionProvider()

    def test_hindi_english_extraction(self, provider):
        hi_cases = [c for c in BENCHMARK_CASES if c["language"] == "hi-en"]
        correct = 0
        for case in hi_cases:
            result = provider.extract_progress(case["input_text"])
            expected = case["expected"]
            
            # Check key fields
            matches = True
            for field, expected_value in expected.items():
                actual_value = getattr(result, field, None)
                if actual_value != expected_value:
                    matches = False
                    break
            
            if matches:
                correct += 1
        
        accuracy = correct / len(hi_cases) if hi_cases else 0
        assert accuracy >= ACCURACY_THRESHOLD, f"Hindi-English accuracy {accuracy:.2f} below threshold {ACCURACY_THRESHOLD}"

    def test_tamil_english_extraction(self, provider):
        ta_cases = [c for c in BENCHMARK_CASES if c["language"] == "ta-en"]
        correct = 0
        for case in ta_cases:
            result = provider.extract_progress(case["input_text"])
            expected = case["expected"]
            
            matches = True
            for field, expected_value in expected.items():
                actual_value = getattr(result, field, None)
                if actual_value != expected_value:
                    matches = False
                    break
            
            if matches:
                correct += 1
        
        accuracy = correct / len(ta_cases) if ta_cases else 0
        assert accuracy >= ACCURACY_THRESHOLD, f"Tamil-English accuracy {accuracy:.2f} below threshold {ACCURACY_THRESHOLD}"

    def test_telugu_english_extraction(self, provider):
        te_cases = [c for c in BENCHMARK_CASES if c["language"] == "te-en"]
        correct = 0
        for case in te_cases:
            result = provider.extract_progress(case["input_text"])
            expected = case["expected"]
            
            matches = True
            for field, expected_value in expected.items():
                actual_value = getattr(result, field, None)
                if actual_value != expected_value:
                    matches = False
                    break
            
            if matches:
                correct += 1
        
        accuracy = correct / len(te_cases) if te_cases else 0
        assert accuracy >= ACCURACY_THRESHOLD, f"Telugu-English accuracy {accuracy:.2f} below threshold {ACCURACY_THRESHOLD}"

    def test_kannada_english_extraction(self, provider):
        kn_cases = [c for c in BENCHMARK_CASES if c["language"] == "kn-en"]
        correct = 0
        for case in kn_cases:
            result = provider.extract_progress(case["input_text"])
            expected = case["expected"]
            
            matches = True
            for field, expected_value in expected.items():
                actual_value = getattr(result, field, None)
                if actual_value != expected_value:
                    matches = False
                    break
            
            if matches:
                correct += 1
        
        accuracy = correct / len(kn_cases) if kn_cases else 0
        assert accuracy >= ACCURACY_THRESHOLD, f"Kannada-English accuracy {accuracy:.2f} below threshold {ACCURACY_THRESHOLD}"

    def test_mixed_language_extraction(self, provider):
        mixed_cases = [c for c in BENCHMARK_CASES if c["language"] == "mixed"]
        correct = 0
        for case in mixed_cases:
            result = provider.extract_progress(case["input_text"])
            expected = case["expected"]
            
            matches = True
            for field, expected_value in expected.items():
                actual_value = getattr(result, field, None)
                if actual_value != expected_value:
                    matches = False
                    break
            
            if matches:
                correct += 1
        
        accuracy = correct / len(mixed_cases) if mixed_cases else 0
        assert accuracy >= ACCURACY_THRESHOLD, f"Mixed language accuracy {accuracy:.2f} below threshold {ACCURACY_THRESHOLD}"

    def test_overall_accuracy(self, provider):
        correct = 0
        for case in BENCHMARK_CASES:
            result = provider.extract_progress(case["input_text"])
            expected = case["expected"]
            
            matches = True
            for field, expected_value in expected.items():
                actual_value = getattr(result, field, None)
                if actual_value != expected_value:
                    matches = False
                    break
            
            if matches:
                correct += 1
        
        accuracy = correct / len(BENCHMARK_CASES)
        assert accuracy >= ACCURACY_THRESHOLD, f"Overall multilingual accuracy {accuracy:.2f} below threshold {ACCURACY_THRESHOLD}"

    def test_agent_chat_hindi(self, provider):
        result = provider.extract_agent_chat("Aaj piping team ne XX-101 spool ka erection start kiya 9:30 baje Area B mein")
        assert result.activity_reference == "XX-101 spool erection"
        assert result.event_type == "START"
        assert result.event_time == "09:30"
        assert result.discipline == "Piping"
        assert result.location == "Area B"
        assert result.equipment_tag == "XX-101"

    def test_agent_chat_tamil(self, provider):
        result = provider.extract_agent_chat("Innum piping team XX-103 spool erection start pannirukku 8:00 mani Area D la")
        assert result.activity_reference == "XX-103 spool erection"
        assert result.event_type == "START"
        assert result.event_time == "08:00"
        assert result.discipline == "Piping"
        assert result.location == "Area D"
        assert result.equipment_tag == "XX-103"

    def test_agent_chat_telugu(self, provider):
        result = provider.extract_agent_chat("Ippudu piping team XX-104 spool erection start chesaru 11:00 Area F lo")
        assert result.activity_reference == "XX-104 spool erection"
        assert result.event_type == "START"
        assert result.event_time == "11:00"
        assert result.discipline == "Piping"
        assert result.location == "Area F"
        assert result.equipment_tag == "XX-104"

    def test_agent_chat_kannada(self, provider):
        result = provider.extract_agent_chat("Ivattu piping team XX-109 spool erection start madidaru 9:00 AM Area L alli")
        assert result.activity_reference == "XX-109 spool erection"
        assert result.event_type == "START"
        assert result.event_time == "09:00"
        assert result.discipline == "Piping"
        assert result.location == "Area L"
        assert result.equipment_tag == "XX-109"

    def test_event_type_keywords_multilingual(self, provider):
        test_cases = [
            # Hindi
            ("shuru kiya", "START"),
            ("chal raha", "PROGRESS"),
            ("complete ho gaya", "COMPLETE"),
            ("delay", "DELAY"),
            ("hold", "HOLD"),
            # Tamil
            ("start pannirukku", "START"),
            ("seiyum", "PROGRESS"),
            ("mudichiruku", "COMPLETE"),
            ("delay aagiruku", "DELAY"),
            # Telugu
            ("start chesaru", "START"),
            ("chestunaru", "PROGRESS"),
            ("ayyindi", "COMPLETE"),
            ("delay ayyindi", "DELAY"),
            # Kannada
            ("start madidaru", "START"),
            ("maadutiddare", "PROGRESS"),
            ("aayithu", "COMPLETE"),
            ("delay aayithu", "DELAY"),
            ("hold aayithu", "HOLD"),
        ]
        
        for text, expected_type in test_cases:
            result = provider.extract_progress(text)
            assert result.event_type == expected_type, f"Failed for '{text}': expected {expected_type}, got {result.event_type}"

    def test_time_formats_multilingual(self, provider):
        test_cases = [
            ("9:30 baje", "09:30"),
            ("8:00 mani", "08:00"),
            ("11:00", "11:00"),
            ("9:00 AM", "09:00"),
            ("10:30", "10:30"),
        ]
        
        for text, expected_time in test_cases:
            result = provider.extract_progress(f"started work at {text}")
            assert result.event_time == expected_time, f"Failed for '{text}': expected {expected_time}, got {result.event_time}"

    def test_location_patterns_multilingual(self, provider):
        test_cases = [
            ("Area B mein", "Area B"),
            ("Area D la", "Area D"),
            ("Area F lo", "Area F"),
            ("Area L alli", "Area L"),
        ]
        
        for text, expected_location in test_cases:
            result = provider.extract_progress(f"started work in {text}")
            assert result.location == expected_location, f"Failed for '{text}': expected {expected_location}, got {result.location}"

    def test_date_keywords_multilingual(self, provider):
        from datetime import date, timedelta
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        test_cases = [
            ("aaj", today),
            ("today", today),
            ("kal", tomorrow),
            ("naalai", tomorrow),
            ("repu", tomorrow),
            ("nale", tomorrow),
        ]
        
        for text, expected_date in test_cases:
            result = provider.extract_progress(f"work {text}")
            assert result.event_date == expected_date, f"Failed for '{text}': expected {expected_date}, got {result.event_date}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])