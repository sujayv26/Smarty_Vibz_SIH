from dataclasses import dataclass
from datetime import date
from typing import List, Optional
from app.matching.schemas import MatchCategory, BenchmarkReport, BenchmarkSummary
from app.models.progress import ProgressEvent
from app.models.schedule import ScheduleActivity
from app.matching.engine import run_matching
from sqlalchemy.orm import Session


@dataclass
class BenchmarkCase:
    raw_text: str
    event_type: str
    event_date: Optional[date]
    discipline: Optional[str]
    location: Optional[str]
    equipment_tag: Optional[str]
    expected_activity_code: Optional[str]
    category: MatchCategory


BENCHMARK_CASES: List[BenchmarkCase] = [
    # EXACT_MATCH: 15 cases
    BenchmarkCase(
        raw_text="Started erection of XX-101 spool at 9:30 AM in Area B",
        event_type="START", event_date=date(2026, 8, 30),
        discipline="Piping", location="Area B", equipment_tag="XX-101",
        expected_activity_code="PIP-1023", category=MatchCategory.EXACT_MATCH
    ),
    BenchmarkCase(
        raw_text="Install Support for XX-101 completed today",
        event_type="COMPLETE", event_date=date(2026, 8, 20),
        discipline="Piping", location="Area B", equipment_tag="XX-101",
        expected_activity_code="PIP-1027", category=MatchCategory.EXACT_MATCH
    ),
    BenchmarkCase(
        raw_text="Inspect XX-101 piping completed",
        event_type="COMPLETE", event_date=date(2026, 9, 3),
        discipline="Piping", location="Area B", equipment_tag="XX-101",
        expected_activity_code="PIP-1042", category=MatchCategory.EXACT_MATCH
    ),
    BenchmarkCase(
        raw_text="Hydrotest Line XX-101 started",
        event_type="START", event_date=date(2026, 9, 5),
        discipline="Piping", location="Area B", equipment_tag="XX-101",
        expected_activity_code="PIP-1050", category=MatchCategory.EXACT_MATCH
    ),
    BenchmarkCase(
        raw_text="Install Pump P-101 completed at Pump House",
        event_type="COMPLETE", event_date=date(2026, 9, 5),
        discipline="Mechanical", location="Pump House", equipment_tag="P-101",
        expected_activity_code="MEC-2011", category=MatchCategory.EXACT_MATCH
    ),
    BenchmarkCase(
        raw_text="Align Pump P-101 started",
        event_type="START", event_date=date(2026, 9, 6),
        discipline="Mechanical", location="Pump House", equipment_tag="P-101",
        expected_activity_code="MEC-2012", category=MatchCategory.EXACT_MATCH
    ),
    BenchmarkCase(
        raw_text="Construct Foundation A1 concrete pouring in progress",
        event_type="PROGRESS", event_date=date(2026, 8, 10),
        discipline="Civil", location="Area C", equipment_tag="A1",
        expected_activity_code="CIV-3011", category=MatchCategory.EXACT_MATCH
    ),
    BenchmarkCase(
        raw_text="Construct Foundation A2 completed",
        event_type="COMPLETE", event_date=date(2026, 8, 25),
        discipline="Civil", location="Area C", equipment_tag="A2",
        expected_activity_code="CIV-3012", category=MatchCategory.EXACT_MATCH
    ),
    BenchmarkCase(
        raw_text="Erect Structural Steel Grid 1 started",
        event_type="START", event_date=date(2026, 8, 20),
        discipline="Civil", location="Area A", equipment_tag="Grid 1",
        expected_activity_code="CIV-3021", category=MatchCategory.EXACT_MATCH
    ),
    BenchmarkCase(
        raw_text="Cable Pulling for Substation SUB-1 in progress",
        event_type="PROGRESS", event_date=date(2026, 8, 25),
        discipline="Electrical", location="Substation", equipment_tag="SUB-1",
        expected_activity_code="ELE-4011", category=MatchCategory.EXACT_MATCH
    ),
    BenchmarkCase(
        raw_text="Terminate Cables SUB-1 completed",
        event_type="COMPLETE", event_date=date(2026, 9, 10),
        discipline="Electrical", location="Substation", equipment_tag="SUB-1",
        expected_activity_code="ELE-4012", category=MatchCategory.EXACT_MATCH
    ),
    BenchmarkCase(
        raw_text="Install MCC Panel MCC-1 started",
        event_type="START", event_date=date(2026, 8, 25),
        discipline="Electrical", location="Substation", equipment_tag="MCC-1",
        expected_activity_code="ELE-4021", category=MatchCategory.EXACT_MATCH
    ),
    BenchmarkCase(
        raw_text="Install Instrument Tubing started",
        event_type="START", event_date=date(2026, 9, 2),
        discipline="Instrumentation", location="Area D", equipment_tag=None,
        expected_activity_code="INS-5011", category=MatchCategory.EXACT_MATCH
    ),
    BenchmarkCase(
        raw_text="Calibrate Transmitters completed",
        event_type="COMPLETE", event_date=date(2026, 9, 20),
        discipline="Instrumentation", location="Area D", equipment_tag=None,
        expected_activity_code="INS-5012", category=MatchCategory.EXACT_MATCH
    ),
    BenchmarkCase(
        raw_text="Install Compressor C-101 completed",
        event_type="COMPLETE", event_date=date(2026, 9, 15),
        discipline="Mechanical", location="Compressor House", equipment_tag="C-101",
        expected_activity_code="MEC-2021", category=MatchCategory.EXACT_MATCH
    ),

    # FUZZY_WORDING: 10 cases
    BenchmarkCase(
        raw_text="Began spool erection work on XX-101 line",
        event_type="START", event_date=date(2026, 8, 30),
        discipline="Piping", location="Area B", equipment_tag="XX-101",
        expected_activity_code="PIP-1023", category=MatchCategory.FUZZY_WORDING
    ),
    BenchmarkCase(
        raw_text="Support installation for XX-101 finished",
        event_type="COMPLETE", event_date=date(2026, 8, 20),
        discipline="Piping", location="Area B", equipment_tag="XX-101",
        expected_activity_code="PIP-1027", category=MatchCategory.FUZZY_WORDING
    ),
    BenchmarkCase(
        raw_text="XX-101 inspection done by piping team",
        event_type="COMPLETE", event_date=date(2026, 9, 3),
        discipline="Piping", location="Area B", equipment_tag="XX-101",
        expected_activity_code="PIP-1042", category=MatchCategory.FUZZY_WORDING
    ),
    BenchmarkCase(
        raw_text="P-101 pump installation finished at pump house",
        event_type="COMPLETE", event_date=date(2026, 9, 5),
        discipline="Mechanical", location="Pump House", equipment_tag="P-101",
        expected_activity_code="MEC-2011", category=MatchCategory.FUZZY_WORDING
    ),
    BenchmarkCase(
        raw_text="Pump P-101 alignment work began",
        event_type="START", event_date=date(2026, 9, 6),
        discipline="Mechanical", location="Pump House", equipment_tag="P-101",
        expected_activity_code="MEC-2012", category=MatchCategory.FUZZY_WORDING
    ),
    BenchmarkCase(
        raw_text="Foundation A1 concrete pour ongoing",
        event_type="PROGRESS", event_date=date(2026, 8, 10),
        discipline="Civil", location="Area C", equipment_tag="A1",
        expected_activity_code="CIV-3011", category=MatchCategory.FUZZY_WORDING
    ),
    BenchmarkCase(
        raw_text="Steel erection Grid 1 commenced",
        event_type="START", event_date=date(2026, 8, 20),
        discipline="Civil", location="Area A", equipment_tag="Grid 1",
        expected_activity_code="CIV-3021", category=MatchCategory.FUZZY_WORDING
    ),
    BenchmarkCase(
        raw_text="Cable pull SUB-1 substation in progress",
        event_type="PROGRESS", event_date=date(2026, 8, 25),
        discipline="Electrical", location="Substation", equipment_tag="SUB-1",
        expected_activity_code="ELE-4011", category=MatchCategory.FUZZY_WORDING
    ),
    BenchmarkCase(
        raw_text="Cable termination SUB-1 finished",
        event_type="COMPLETE", event_date=date(2026, 9, 10),
        discipline="Electrical", location="Substation", equipment_tag="SUB-1",
        expected_activity_code="ELE-4012", category=MatchCategory.FUZZY_WORDING
    ),
    BenchmarkCase(
        raw_text="MCC-1 panel install kicked off",
        event_type="START", event_date=date(2026, 8, 25),
        discipline="Electrical", location="Substation", equipment_tag="MCC-1",
        expected_activity_code="ELE-4021", category=MatchCategory.FUZZY_WORDING
    ),

    # AMBIGUOUS_TAG: 10 cases
    BenchmarkCase(
        raw_text="Started work on XX-101 piping spool",
        event_type="START", event_date=date(2026, 8, 30),
        discipline="Piping", location="Area B", equipment_tag="XX-101",
        expected_activity_code="PIP-1023", category=MatchCategory.AMBIGUOUS_TAG
    ),
    BenchmarkCase(
        raw_text="XX-101 support installation ongoing",
        event_type="PROGRESS", event_date=date(2026, 8, 15),
        discipline="Piping", location="Area B", equipment_tag="XX-101",
        expected_activity_code="PIP-1027", category=MatchCategory.AMBIGUOUS_TAG
    ),
    BenchmarkCase(
        raw_text="XX-101 inspection completed by QA",
        event_type="COMPLETE", event_date=date(2026, 9, 3),
        discipline="Piping", location="Area B", equipment_tag="XX-101",
        expected_activity_code="PIP-1042", category=MatchCategory.AMBIGUOUS_TAG
    ),
    BenchmarkCase(
        raw_text="Hydrotest on XX-101 line started",
        event_type="START", event_date=date(2026, 9, 5),
        discipline="Piping", location="Area B", equipment_tag="XX-101",
        expected_activity_code="PIP-1050", category=MatchCategory.AMBIGUOUS_TAG
    ),
    BenchmarkCase(
        raw_text="Work on XX-102 spool erection began",
        event_type="START", event_date=date(2026, 8, 30),
        discipline="Piping", location="Area B", equipment_tag="XX-102",
        expected_activity_code="PIP-1060", category=MatchCategory.AMBIGUOUS_TAG
    ),
    BenchmarkCase(
        raw_text="Support install for XX-102 done",
        event_type="COMPLETE", event_date=date(2026, 8, 25),
        discipline="Piping", location="Area B", equipment_tag="XX-102",
        expected_activity_code="PIP-1065", category=MatchCategory.AMBIGUOUS_TAG
    ),
    BenchmarkCase(
        raw_text="Foundation B1 concrete work started",
        event_type="START", event_date=date(2026, 8, 15),
        discipline="Civil", location="Area B", equipment_tag="B1",
        expected_activity_code="CIV-3031", category=MatchCategory.AMBIGUOUS_TAG
    ),
    BenchmarkCase(
        raw_text="Foundation A1 concrete work completed",
        event_type="COMPLETE", event_date=date(2026, 8, 15),
        discipline="Civil", location="Area C", equipment_tag="A1",
        expected_activity_code="CIV-3011", category=MatchCategory.AMBIGUOUS_TAG
    ),
    BenchmarkCase(
        raw_text="Pump P-101 work started",
        event_type="START", event_date=date(2026, 8, 25),
        discipline="Mechanical", location="Pump House", equipment_tag="P-101",
        expected_activity_code="MEC-2011", category=MatchCategory.AMBIGUOUS_TAG
    ),
    BenchmarkCase(
        raw_text="P-101 alignment and testing done",
        event_type="COMPLETE", event_date=date(2026, 9, 10),
        discipline="Mechanical", location="Pump House", equipment_tag="P-101",
        expected_activity_code="MEC-2012", category=MatchCategory.AMBIGUOUS_TAG
    ),

    # MISSING_FIELDS: 5 cases
    BenchmarkCase(
        raw_text="Started piping work",
        event_type="START", event_date=date(2026, 8, 30),
        discipline="Piping", location=None, equipment_tag=None,
        expected_activity_code="PIP-1023", category=MatchCategory.MISSING_FIELDS
    ),
    BenchmarkCase(
        raw_text="Civil work completed today",
        event_type="COMPLETE", event_date=date(2026, 8, 25),
        discipline="Civil", location=None, equipment_tag=None,
        expected_activity_code="CIV-3012", category=MatchCategory.MISSING_FIELDS
    ),
    BenchmarkCase(
        raw_text="Mechanical installation in progress",
        event_type="PROGRESS", event_date=date(2026, 9, 1),
        discipline="Mechanical", location=None, equipment_tag=None,
        expected_activity_code="MEC-2011", category=MatchCategory.MISSING_FIELDS
    ),
    BenchmarkCase(
        raw_text="Electrical cable work done",
        event_type="COMPLETE", event_date=date(2026, 9, 10),
        discipline="Electrical", location=None, equipment_tag=None,
        expected_activity_code="ELE-4012", category=MatchCategory.MISSING_FIELDS
    ),
    BenchmarkCase(
        raw_text="Instrumentation calibration finished",
        event_type="COMPLETE", event_date=date(2026, 9, 20),
        discipline="Instrumentation", location=None, equipment_tag=None,
        expected_activity_code="INS-5012", category=MatchCategory.MISSING_FIELDS
    ),

    # NO_MATCH: 5 cases
    BenchmarkCase(
        raw_text="Office furniture delivery received",
        event_type="COMPLETE", event_date=date(2026, 8, 15),
        discipline="Admin", location="Office", equipment_tag=None,
        expected_activity_code=None, category=MatchCategory.NO_MATCH
    ),
    BenchmarkCase(
        raw_text="Safety meeting held at site office",
        event_type="COMPLETE", event_date=date(2026, 8, 20),
        discipline="Safety", location="Site Office", equipment_tag=None,
        expected_activity_code=None, category=MatchCategory.NO_MATCH
    ),
    BenchmarkCase(
        raw_text="Material delivery for warehouse",
        event_type="START", event_date=date(2026, 9, 1),
        discipline="Logistics", location="Warehouse", equipment_tag=None,
        expected_activity_code=None, category=MatchCategory.NO_MATCH
    ),
    BenchmarkCase(
        raw_text="Canteen renovation started",
        event_type="START", event_date=date(2026, 8, 10),
        discipline="Facilities", location="Canteen", equipment_tag=None,
        expected_activity_code=None, category=MatchCategory.NO_MATCH
    ),
    BenchmarkCase(
        raw_text="IT network setup completed",
        event_type="COMPLETE", event_date=date(2026, 9, 5),
        discipline="IT", location="Server Room", equipment_tag=None,
        expected_activity_code=None, category=MatchCategory.NO_MATCH
    ),

    # MULTI_DISCIPLINE: 5 cases
    BenchmarkCase(
        raw_text="Piping and Civil interface work at Area B for XX-101",
        event_type="START", event_date=date(2026, 8, 30),
        discipline="Piping", location="Area B", equipment_tag="XX-101",
        expected_activity_code="PIP-1023", category=MatchCategory.MULTI_DISCIPLINE
    ),
    BenchmarkCase(
        raw_text="Mechanical and Electrical coordination for P-101 install",
        event_type="PROGRESS", event_date=date(2026, 8, 25),
        discipline="Mechanical", location="Pump House", equipment_tag="P-101",
        expected_activity_code="MEC-2011", category=MatchCategory.MULTI_DISCIPLINE
    ),
    BenchmarkCase(
        raw_text="Civil foundation and Structural steel erection overlap",
        event_type="PROGRESS", event_date=date(2026, 8, 20),
        discipline="Civil", location="Area A", equipment_tag="Grid 1",
        expected_activity_code="CIV-3021", category=MatchCategory.MULTI_DISCIPLINE
    ),
    BenchmarkCase(
        raw_text="Electrical and Instrumentation cable and tubing work",
        event_type="START", event_date=date(2026, 9, 1),
        discipline="Electrical", location="Substation", equipment_tag="SUB-1",
        expected_activity_code="ELE-4011", category=MatchCategory.MULTI_DISCIPLINE
    ),
    BenchmarkCase(
        raw_text="Piping hydrotest and Mechanical alignment combined",
        event_type="COMPLETE", event_date=date(2026, 9, 10),
        discipline="Piping", location="Area B", equipment_tag="XX-101",
        expected_activity_code="PIP-1050", category=MatchCategory.MULTI_DISCIPLINE
    ),
]


def create_progress_event(db: Session, case: BenchmarkCase) -> ProgressEvent:
    event = ProgressEvent(
        raw_text=case.raw_text,
        activity_reference=None,
        event_type=case.event_type,
        event_date=case.event_date,
        event_time=None,
        discipline=case.discipline,
        location=case.location,
        equipment_tag=case.equipment_tag,
        source_type="FREE_TEXT",
        source_file=None,
        session_id=None,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def run_benchmark(db: Session) -> BenchmarkSummary:
    reports = []
    top1_correct = 0
    top3_correct = 0
    category_counts = {}
    category_top1 = {}
    category_top3 = {}
    
    for case in BENCHMARK_CASES:
        event = create_progress_event(db, case)
        result = run_matching(db, event.id)
        
        top1_match = None
        top3_matches = []
        top1_is_correct = False
        top3_is_correct = False
        final_scores = []
        
        if result and result.top_matches:
            top1_match = result.top_matches[0].activity_code
            top3_matches = [m.activity_code for m in result.top_matches]
            final_scores = [m.final_score for m in result.top_matches]
            
            if case.expected_activity_code:
                if top1_match == case.expected_activity_code:
                    top1_is_correct = True
                    top1_correct += 1
                if case.expected_activity_code in top3_matches:
                    top3_is_correct = True
                    top3_correct += 1
            else:
                top1_is_correct = False
                top3_is_correct = False
        
        cat = case.category.value
        category_counts[cat] = category_counts.get(cat, 0) + 1
        category_top1[cat] = category_top1.get(cat, 0) + (1 if top1_is_correct else 0)
        category_top3[cat] = category_top3.get(cat, 0) + (1 if top3_is_correct else 0)
        
        reports.append(BenchmarkReport(
            progress_event_id=event.id,
            expected_activity_code=case.expected_activity_code,
            category=case.category,
            top1_match=top1_match,
            top3_matches=top3_matches,
            top1_correct=top1_is_correct,
            top3_correct=top3_is_correct,
            final_scores=final_scores,
        ))
    
    total = len(BENCHMARK_CASES)
    top1_acc = top1_correct / total if total > 0 else 0.0
    top3_acc = top3_correct / total if total > 0 else 0.0
    
    category_results = {}
    for cat in category_counts:
        category_results[cat] = {
            "count": category_counts[cat],
            "top1_accuracy": category_top1.get(cat, 0) / category_counts[cat] if category_counts[cat] > 0 else 0.0,
            "top3_accuracy": category_top3.get(cat, 0) / category_counts[cat] if category_counts[cat] > 0 else 0.0,
        }
    
    return BenchmarkSummary(
        total_reports=total,
        top1_accuracy=round(top1_acc, 4),
        top3_accuracy=round(top3_acc, 4),
        category_results=category_results,
        reports=reports,
    )