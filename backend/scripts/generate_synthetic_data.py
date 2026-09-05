#!/usr/bin/env python3
"""Generate synthetic data for ConSight demo environment.

Creates realistic multi-discipline WBS tree, field events, delays, 
and productivity benchmarks directly in PostgreSQL.
"""

import argparse
import random
import sys
import os
from datetime import date, timedelta, datetime
from typing import List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import SessionLocal
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.models.project import Project
from app.models.ingestion_source import IngestionSource
from app.models.wbs_node import WBSNode
from app.models.schedule import ScheduleActivity
from app.models.progress import ProgressEvent
from app.models.confidence import ConfidenceResult, PlannerReview, AuditRecord, ConfidenceLevel, DecisionType, ActorType
from app.models.event_wbs_match import EventWBSMatch, MatchType
from app.models.glossary_mapping import GlossaryMapping
from app.models.delay_reason import DelayReason, DelayCategory
from app.models.productivity_benchmark import ProductivityBenchmark
from app.models.audit_log import AuditLog, AuditAction
from app.core.security import get_password_hash


DISCIPLINES = ["Civil", "Structural", "Mechanical", "Electrical", "Piping", "Instrumentation", "Architectural"]
EVENT_TYPES = ["START", "PROGRESS", "COMPLETE", "DELAY", "HOLD", "RESUME", "REWORK", "INSPECT"]
SOURCE_TYPES = ["VOICE", "TIME_AGENT", "TEXT_DIARY", "SPREADSHEET", "PDF_OCR", "PMIS_EXPORT", "WHATSAPP"]
WBS_LEVELS = {
    "L1": ["Civil", "Structural", "MEP", "Finishes"],
    "L2": {
        "Civil": ["Earthworks", "Foundations", "Roadworks", "Drainage"],
        "Structural": ["Columns", "Beams", "Slabs", "Walls"],
        "MEP": ["HVAC", "Electrical", "Plumbing", "Fire Protection"],
        "Finishes": ["Flooring", "Ceilings", "Partitions", "Painting"],
    },
    "L3": {
        "Earthworks": ["Excavation", "Backfill", "Compaction", "Grading"],
        "Foundations": ["Piles", "Pile Caps", "Footings", "Mat Foundation"],
        "Roadworks": ["Subbase", "Base Course", "Asphalt", "Curb & Gutter"],
        "Drainage": ["Storm Sewer", "Sanitary Sewer", "Manholes", "Catch Basins"],
        "Columns": ["Column Rebar", "Column Formwork", "Column Pour", "Column Strip"],
        "Beams": ["Beam Rebar", "Beam Formwork", "Beam Pour", "Beam Strip"],
        "Slabs": ["Slab Prep", "Slab Rebar", "Slab Pour", "Slab Cure"],
        "Walls": ["Wall Rebar", "Wall Formwork", "Wall Pour", "Wall Strip"],
        "HVAC": ["Ductwork", "AHU Install", "Chiller Install", "Controls"],
        "Electrical": ["Conduit", "Cable Pull", "Panel Install", "Terminations"],
        "Plumbing": ["Piping Rough-in", "Fixture Install", "Testing", "Insulation"],
        "Fire Protection": ["Sprinkler Mains", "Sprinkler Heads", "Pump Install", "Testing"],
        "Flooring": ["Tile", "Carpet", "Vinyl", "Concrete Polish"],
        "Ceilings": ["Grid", "Tile", "Access Panels", "Clouds"],
        "Partitions": ["Metal Studs", "Drywall", "Taping", "Door Frames"],
        "Painting": ["Prime", "Finish Coat", "Touch-up", "Special Coatings"],
    },
}


def get_or_create_org(db: Session, name: str, slug: str) -> Organization:
    org = db.query(Organization).filter(Organization.slug == slug).first()
    if not org:
        org = Organization(name=name, slug=slug, description=f"{name} - Demo Organization")
        db.add(org)
        db.commit()
        db.refresh(org)
    return org


def get_or_create_project(db: Session, org_id: int, code: str, name: str) -> Project:
    proj = db.query(Project).filter(Project.code == code).first()
    if not proj:
        proj = Project(
            name=name,
            code=code,
            description=f"{name} - Demo Project",
            organization_id=org_id,
            location="Demo City, Demo State",
            latitude="12.3456",
            longitude="78.9012",
            start_date=date.today() - timedelta(days=180),
            end_date=date.today() + timedelta(days=180),
        )
        db.add(proj)
        db.commit()
        db.refresh(proj)
    return proj


def get_or_create_users(db: Session, org_id: int) -> Dict[str, User]:
    users = {}
    roles_data = [
        ("admin@demo.com", "admin123", "System Admin", UserRole.SYSTEM_ADMIN, None),
        ("contractor@demo.com", "contractor123", "Contractor Admin", UserRole.CONTRACTOR_ADMIN, org_id),
        ("controls@demo.com", "controls123", "Project Controls", UserRole.PROJECT_CONTROLS, org_id),
        ("planner@demo.com", "planner123", "Discipline Planner", UserRole.DISCIPLINE_PLANNER, org_id),
        ("supervisor@demo.com", "supervisor123", "Site Supervisor", UserRole.SITE_SUPERVISOR, org_id),
    ]
    for email, pwd, name, role, org in roles_data:
        u = db.query(User).filter(User.email == email).first()
        if not u:
            u = User(
                email=email,
                hashed_password=get_password_hash(pwd),
                full_name=name,
                role=role,
                organization_id=org or org_id,
                discipline=random.choice(DISCIPLINES) if role == UserRole.DISCIPLINE_PLANNER else None,
                preferred_language=random.choice(["en", "hi", "ta", "te"]),
            )
            db.add(u)
        users[role.value] = u
    db.commit()
    for u in users.values():
        db.refresh(u)
    return users


def get_or_create_sources(db: Session) -> Dict[str, IngestionSource]:
    sources = {}
    source_data = [
        ("VOICE", "Voice/Time-Agent", "Supervisor voice notes via Time-Agent"),
        ("TIME_AGENT", "Time-Agent Chat", "Conversational Time-Agent chat"),
        ("TEXT_DIARY", "Text Diary", "Manual text diary entries"),
        ("SPREADSHEET", "Spreadsheet Upload", "Excel/CSV progress uploads"),
        ("PDF_OCR", "PDF/OCR Scan", "Scanned daily diaries via OCR"),
        ("PMIS_EXPORT", "PMIS Export", "Automated PMIS schedule exports"),
        ("WHATSAPP", "WhatsApp", "WhatsApp Business Cloud API messages"),
    ]
    for code, name, desc in source_data:
        src = db.query(IngestionSource).filter(IngestionSource.code == code).first()
        if not src:
            src = IngestionSource(code=code, name=name, description=desc)
            db.add(src)
        sources[code] = src
    db.commit()
    for src in sources.values():
        db.refresh(src)
    return sources


def build_wbs_tree(db: Session, project_id: int, org_id: int, weeks: int = 12) -> List[WBSNode]:
    """Build a realistic L1-L6 WBS tree with predecessor/successor relationships."""
    nodes = []
    base_date = date.today() - timedelta(weeks=weeks//2)
    activity_counter = 1

    # L1 nodes
    l1_nodes = []
    for i, l1_name in enumerate(WBS_LEVELS["L1"]):
        node = WBSNode(
            project_id=project_id,
            activity_code=f"{l1_name[:3].upper()}.00",
            activity_name=f"{l1_name} Works",
            discipline=l1_name,
            wbs=f"{l1_name[:3].upper()}",
            level=1,
            planned_start=base_date + timedelta(weeks=i*3),
            planned_finish=base_date + timedelta(weeks=i*3 + 10),
            is_unplanned=False,
            is_milestone=(i == 0),
        )
        db.add(node)
        l1_nodes.append(node)
    db.commit()
    for n in l1_nodes:
        db.refresh(n)
        nodes.append(n)

    # L2-L4 nodes
    for l1_node in l1_nodes:
        l1_disc = l1_node.discipline
        if l1_disc not in WBS_LEVELS["L2"]:
            continue
        for j, l2_name in enumerate(WBS_LEVELS["L2"][l1_disc]):
            l2_node = WBSNode(
                project_id=project_id,
                activity_code=f"{l1_node.activity_code}.{j+1:02d}",
                activity_name=f"{l2_name}",
                discipline=l1_disc,
                wbs=f"{l1_node.wbs}.{j+1:02d}",
                level=2,
                parent_id=l1_node.id,
                planned_start=l1_node.planned_start + timedelta(weeks=j),
                planned_finish=l1_node.planned_finish - timedelta(weeks=len(WBS_LEVELS["L2"][l1_disc]) - j),
                is_unplanned=False,
            )
            db.add(l2_node)
            db.commit()
            db.refresh(l2_node)
            nodes.append(l2_node)

            if l2_name in WBS_LEVELS["L3"]:
                for k, l3_name in enumerate(WBS_LEVELS["L3"][l2_name]):
                    l3_node = WBSNode(
                        project_id=project_id,
                        activity_code=f"{l2_node.activity_code}.{k+1:02d}",
                        activity_name=f"{l3_name}",
                        discipline=l1_disc,
                        wbs=f"{l2_node.wbs}.{k+1:02d}",
                        level=3,
                        parent_id=l2_node.id,
                        planned_start=l2_node.planned_start + timedelta(days=k*7),
                        planned_finish=l2_node.planned_start + timedelta(days=k*7 + 10),
                        is_unplanned=False,
                    )
                    db.add(l3_node)
                    db.commit()
                    db.refresh(l3_node)
                    nodes.append(l3_node)

                    # L4: actual work packages
                    for m in range(random.randint(2, 4)):
                        l4_node = WBSNode(
                            project_id=project_id,
                            activity_code=f"{l3_node.activity_code}.{m+1:02d}",
                            activity_name=f"{l3_name} - Package {m+1}",
                            discipline=l1_disc,
                            wbs=f"{l3_node.wbs}.{m+1:02d}",
                            level=4,
                            parent_id=l3_node.id,
                            planned_start=l3_node.planned_start + timedelta(days=m*3),
                            planned_finish=l3_node.planned_start + timedelta(days=m*3 + 5),
                            is_unplanned=False,
                        )
                        db.add(l4_node)
                        db.commit()
                        db.refresh(l4_node)
                        nodes.append(l4_node)

    # Create ScheduleActivity records mirroring WBS nodes for backward compatibility
    for wbs in nodes:
        act = ScheduleActivity(
            organization_id=org_id,
            project_id=project_id,
            activity_code=wbs.activity_code,
            activity_name=wbs.activity_name,
            discipline=wbs.discipline,
            wbs=wbs.wbs,
            planned_start=wbs.planned_start,
            planned_finish=wbs.planned_finish,
            is_unplanned=wbs.is_unplanned,
            external_schedule_id=None,
            source_format="SYNTHETIC",
        )
        db.add(act)
    db.commit()

    return nodes


def generate_field_events(
    db: Session, 
    project_id: int, 
    org_id: int, 
    wbs_nodes: List[WBSNode], 
    users: Dict[str, User],
    sources: Dict[str, IngestionSource],
    weeks: int = 12,
    seed: int = 42,
) -> List[ProgressEvent]:
    """Generate realistic field events across all ingestion sources."""
    random.seed(seed)
    events = []
    supervisor = users.get("SITE_SUPERVISOR")
    planner = users.get("DISCIPLINE_PLANNER")
    
    base_date = date.today() - timedelta(weeks=weeks)
    
    # Select active nodes (level 3-4)
    active_nodes = [n for n in wbs_nodes if n.level >= 3]
    
    for week in range(weeks):
        week_start = base_date + timedelta(weeks=week)
        events_this_week = random.randint(15, 30)
        
        for _ in range(events_this_week):
            wbs = random.choice(active_nodes)
            event_date = week_start + timedelta(days=random.randint(0, 6))
            event_type = random.choices(
                EVENT_TYPES, 
                weights=[0.15, 0.20, 0.15, 0.10, 0.05, 0.05, 0.05, 0.25]
            )[0]
            source_code = random.choice(list(sources.keys()))
            source = sources[source_code]
            
            # Generate realistic raw text based on source type
            raw_text = generate_raw_text(wbs, event_type, event_date, source_code)
            
            event = ProgressEvent(
                organization_id=org_id,
                project_id=project_id,
                user_id=supervisor.id if supervisor else None,
                raw_text=raw_text,
                activity_reference=wbs.activity_name,
                event_type=event_type,
                event_date=event_date,
                event_time=f"{random.randint(6,18):02d}:{random.randint(0,59):02d}",
                discipline=wbs.discipline,
                location=f"Area {random.choice(['A','B','C','D'])}-{random.randint(1,99):02d}",
                equipment_tag=f"{wbs.discipline[:3].upper()}-{random.randint(100,999)}",
                source_type=source_code,
                ingestion_source_id=source.id,
            )
            db.add(event)
            db.commit()
            db.refresh(event)
            events.append(event)
            
            # Generate confidence result and match
            generate_confidence_and_match(db, event, wbs, org_id, project_id)
    
    return events


def generate_raw_text(wbs: WBSNode, event_type: str, event_date: date, source_type: str) -> str:
    """Generate realistic raw text for different source types."""
    templates = {
        "VOICE": [
            f"Today {event_date.strftime('%B %d')} the {wbs.discipline.lower()} team {event_type.lower()} on {wbs.activity_name.lower()} at {wbs.wbs}",
            f"Supervisor reporting {event_type.lower()} of {wbs.activity_name} in area {random.randint(1,5)}",
        ],
        "TIME_AGENT": [
            f"Started {wbs.activity_name} at {event_date}",
            f"{wbs.activity_name} {event_type.lower()} today",
            f"Completed {wbs.activity_name} at area {random.randint(1,5)}",
        ],
        "TEXT_DIARY": [
            f"Diary entry: {wbs.activity_name} - {event_type} on {event_date.strftime('%Y-%m-%d')}",
            f"Work done: {wbs.activity_name} ({event_type})",
        ],
        "SPREADSHEET": [
            f"{event_date},{wbs.discipline},{wbs.activity_name},{event_type}",
        ],
        "PDF_OCR": [
            f"DAILY REPORT\nDate: {event_date}\nDiscipline: {wbs.discipline}\nActivity: {wbs.activity_name}\nStatus: {event_type}",
        ],
        "PMIS_EXPORT": [
            f"PMIS_EXPORT|{wbs.activity_code}|{wbs.activity_name}|{event_type}|{event_date}",
        ],
        "WHATSAPP": [
            f"📍 Site update: {wbs.activity_name} {event_type.lower()} today at {wbs.wbs}. Team on track.",
            f"Progress: {wbs.activity_name} - {event_type} completed. Photos attached.",
        ],
    }
    return random.choice(templates.get(source_type, templates["VOICE"]))


def generate_confidence_and_match(db: Session, event: ProgressEvent, wbs: WBSNode, org_id: int, project_id: int):
    """Generate confidence result and event_wbs_match for an event."""
    # Simulate matching - mostly correct, some ambiguous, some new activity
    match_quality = random.random()
    
    if match_quality > 0.75:
        # High confidence - correct match
        confidence_score = random.uniform(0.85, 0.98)
        confidence_level = ConfidenceLevel.HIGH
        decision = DecisionType.AUTO_MATCH
        match_type = MatchType.EXACT
        wbs_node_id = wbs.id
        progress_pct = random.uniform(80, 100)
    elif match_quality > 0.45:
        # Medium confidence - review needed
        confidence_score = random.uniform(0.60, 0.85)
        confidence_level = ConfidenceLevel.MEDIUM
        decision = DecisionType.APPROVED
        match_type = random.choice([MatchType.FUZZY, MatchType.SEMANTIC, MatchType.CONTEXTUAL])
        wbs_node_id = wbs.id
        progress_pct = random.uniform(40, 80)
    elif match_quality > 0.15:
        # Low confidence - corrected by planner
        confidence_score = random.uniform(0.30, 0.60)
        confidence_level = ConfidenceLevel.LOW
        decision = DecisionType.CORRECTED
        match_type = MatchType.NEW_ACTIVITY
        # Pick a different node
        wbs_node_id = random.choice([n for n in db.query(WBSNode).filter(WBSNode.project_id == project_id).all() if n.id != wbs.id]).id
        progress_pct = random.uniform(10, 40)
    else:
        # New activity created
        confidence_score = random.uniform(0.10, 0.40)
        confidence_level = ConfidenceLevel.LOW
        decision = DecisionType.NEW_ACTIVITY_CREATED
        match_type = MatchType.NEW_ACTIVITY
        wbs_node_id = None
        progress_pct = None
    
    conf = ConfidenceResult(
        progress_event_id=event.id,
        proposed_activity_id=wbs.id if match_quality > 0.15 else None,
        confidence_score=confidence_score,
        confidence_level=confidence_level,
        decision=decision,
        score_gap=random.uniform(0, 0.3),
        exact_identifier_strength=random.uniform(0.7, 1.0) if match_type == MatchType.EXACT else random.uniform(0, 0.5),
        fuzzy_similarity=random.uniform(0.6, 0.9) if match_type == MatchType.FUZZY else random.uniform(0, 0.5),
        semantic_similarity=random.uniform(0.6, 0.9) if match_type == MatchType.SEMANTIC else random.uniform(0, 0.5),
        discipline_compatibility=1.0 if match_quality > 0.45 else random.uniform(0.3, 0.7),
        context_compatibility=random.uniform(0.5, 1.0),
        temporal_compatibility=random.uniform(0.5, 1.0),
        missing_information_penalty=random.uniform(0, 0.2),
        candidate_ambiguity_penalty=random.uniform(0, 0.3) if match_quality < 0.6 else random.uniform(0, 0.1),
    )
    db.add(conf)
    db.commit()
    db.refresh(conf)
    
    # Event-WBS Match
    match = EventWBSMatch(
        progress_event_id=event.id,
        wbs_node_id=wbs_node_id,
        match_type=match_type,
        confidence_score=confidence_score,
        progress_contribution_pct=progress_pct,
        score_breakdown_json=f'{{"exact": {conf.exact_identifier_strength:.2f}, "fuzzy": {conf.fuzzy_similarity:.2f}, "semantic": {conf.semantic_similarity:.2f}, "discipline": {conf.discipline_compatibility:.2f}, "context": {conf.context_compatibility:.2f}, "temporal": {conf.temporal_compatibility:.2f}}}',
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    
    # Planner Review for non-auto-matched
    if decision != DecisionType.AUTO_MATCH:
        review = PlannerReview(
            progress_event_id=event.id,
            proposed_activity_id=wbs.id if match_quality > 0.15 else None,
            final_activity_id=wbs_node_id,
            confidence_score=confidence_score,
            confidence_level=confidence_level,
            status="APPROVED" if decision in [DecisionType.APPROVED, DecisionType.CORRECTED] else "PENDING",
            top_candidates_json=f'[{{"activity_id": {wbs.id}, "score": {confidence_score:.2f}}}]',
            score_breakdown_json=match.score_breakdown_json,
            reviewer_note="Auto-generated review" if decision == DecisionType.APPROVED else "Corrected to match actual work",
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        
        # Audit Record
        audit = AuditRecord(
            progress_event_id=event.id,
            proposed_activity_id=wbs.id,
            final_activity_id=wbs_node_id,
            confidence_score=confidence_score,
            confidence_level=confidence_level,
            decision=decision,
            reviewer_note=review.reviewer_note,
            actor_type=ActorType.PLANNER if decision != DecisionType.AUTO_MATCH else ActorType.SYSTEM,
        )
        db.add(audit)
        db.commit()
    
    # Audit Log
    audit_log = AuditLog(
        organization_id=org_id,
        project_id=project_id,
        user_id=event.user_id,
        action=AuditAction.MATCH,
        entity_type="progress_event",
        entity_id=event.id,
        new_values={
            "confidence_score": confidence_score,
            "match_type": match_type.value,
            "decision": decision.value,
        },
    )
    db.add(audit_log)
    db.commit()


def generate_delays(db: Session, project_id: int, org_id: int, wbs_nodes: List[WBSNode], users: Dict[str, User], seed: int = 42):
    """Generate delay reasons for some activities."""
    random.seed(seed + 100)
    planner = users.get("DISCIPLINE_PLANNER")
    active_nodes = [n for n in wbs_nodes if n.level >= 3]
    
    for _ in range(random.randint(8, 15)):
        wbs = random.choice(active_nodes)
        category = random.choice(list(DelayCategory))
        delay = DelayReason(
            project_id=project_id,
            wbs_node_id=wbs.id,
            category=category,
            description=f"{category.value}: {random.choice(['Late material delivery', 'Weather delay', 'Resource shortage', 'Design change', 'Permit delay', 'Subcontractor delay'])} on {wbs.activity_name}",
            impact_days=random.randint(1, 14),
            is_critical_path=random.random() > 0.7,
            reported_by=planner.id if planner else None,
        )
        db.add(delay)
    db.commit()


def generate_productivity_benchmarks(db: Session, org_id: int, project_id: int, seed: int = 42):
    """Generate productivity benchmarks from historical data."""
    random.seed(seed + 200)
    activities = [
        ("Excavation", "m3", 100, 15),
        ("Backfill", "m3", 80, 12),
        ("Concrete Pour", "m3", 50, 8),
        ("Formwork", "m2", 200, 20),
        ("Rebar Installation", "ton", 5, 10),
        ("Piping Install", "m", 50, 15),
        ("Ductwork", "m", 80, 12),
        ("Cable Pull", "m", 200, 8),
        ("Tile Install", "m2", 30, 10),
        ("Painting", "m2", 100, 5),
    ]
    
    for act_type, unit, qty, dur in activities:
        discipline = random.choice(DISCIPLINES)
        planned_qty = qty * random.uniform(0.8, 1.2)
        actual_qty = planned_qty * random.uniform(0.7, 1.1)
        planned_dur = dur * random.uniform(0.9, 1.1)
        actual_dur = planned_dur * random.uniform(0.8, 1.3)
        
        bench = ProductivityBenchmark(
            organization_id=org_id,
            project_id=project_id,
            discipline=discipline,
            activity_type=act_type,
            unit=unit,
            planned_quantity=planned_qty,
            actual_quantity=actual_qty,
            planned_duration_days=planned_dur,
            actual_duration_days=actual_dur,
            productivity_rate=(actual_qty / actual_dur) if actual_dur > 0 else None,
            sample_size=random.randint(5, 20),
            period_start=date.today() - timedelta(days=random.randint(30, 180)),
            period_end=date.today() - timedelta(days=random.randint(1, 30)),
        )
        db.add(bench)
    db.commit()


def generate_glossary_mappings(db: Session, org_id: int, project_id: int, seed: int = 42):
    """Generate glossary mappings for code-mixed terms."""
    random.seed(seed + 300)
    mappings = [
        ("chalu", "START", "Civil", "Hindi/English code-mixed for start"),
        ("bandh", "COMPLETE", "Civil", "Hindi/English code-mixed for complete"),
        ("kaam chalu", "START", "General", "Work started"),
        ("kaam khatam", "COMPLETE", "General", "Work finished"),
        ("shuru", "START", "General", "Hindi for start"),
        ("khatam", "COMPLETE", "General", "Hindi for complete"),
        ("erection start", "START", "Structural", "Steel erection begun"),
        ("pour complete", "COMPLETE", "Civil", "Concrete pour finished"),
        ("hydrotest done", "COMPLETE", "Piping", "Hydrostatic test passed"),
        ("energized", "COMPLETE", "Electrical", "Circuit energized"),
    ]
    for source, std, disc, ctx in mappings:
        mapping = GlossaryMapping(
            organization_id=org_id,
            project_id=project_id,
            source_term=source,
            standardized_term=std,
            discipline=disc,
            context=ctx,
        )
        db.add(mapping)
    db.commit()


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic ConSight data")
    parser.add_argument("--project", default="DEMO-001", help="Project code")
    parser.add_argument("--org", default="demo", help="Organization slug")
    parser.add_argument("--weeks", type=int, default=12, help="Weeks of data to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--reset", action="store_true", help="Delete existing data first")
    args = parser.parse_args()

    db: Session = SessionLocal()
    try:
        print(f"Generating synthetic data for project={args.project}, org={args.org}, weeks={args.weeks}, seed={args.seed}")
        
        # Get or create org
        org = get_or_create_org(db, "Demo Construction Co.", args.org)
        print(f"Organization: {org.name} (id={org.id})")
        
        # Get or create project
        proj = get_or_create_project(db, org.id, args.project, "Demo Highway Project")
        print(f"Project: {proj.name} (id={proj.id})")
        
        # Get or create users
        users = get_or_create_users(db, org.id)
        print(f"Users: {len(users)} created/found")
        
        # Get or create sources
        sources = get_or_create_sources(db)
        print(f"Ingestion sources: {len(sources)}")
        
        if args.reset:
            # Delete existing data for this project
            # First delete records with direct project_id
            for model in [ProgressEvent, DelayReason, ProductivityBenchmark, GlossaryMapping, AuditLog, WBSNode, ScheduleActivity]:
                db.query(model).filter(model.project_id == proj.id).delete()
            # Then delete via joins for models without project_id
            event_ids = [e.id for e in db.query(ProgressEvent).filter(ProgressEvent.project_id == proj.id).all()]
            if event_ids:
                for model in [ConfidenceResult, PlannerReview, AuditRecord, EventWBSMatch]:
                    db.query(model).filter(model.progress_event_id.in_(event_ids)).delete()
            db.commit()
            print("Reset existing project data")
        
        # Build WBS tree
        print("Building WBS tree...")
        wbs_nodes = build_wbs_tree(db, proj.id, org.id, args.weeks)
        print(f"Created {len(wbs_nodes)} WBS nodes")
        
        # Generate field events
        print("Generating field events...")
        events = generate_field_events(db, proj.id, org.id, wbs_nodes, users, sources, args.weeks, args.seed)
        print(f"Created {len(events)} field events")
        
        # Generate delays
        print("Generating delays...")
        generate_delays(db, proj.id, org.id, wbs_nodes, users, args.seed)
        print("Delays created")
        
        # Generate productivity benchmarks
        print("Generating productivity benchmarks...")
        generate_productivity_benchmarks(db, org.id, proj.id, args.seed)
        print("Benchmarks created")
        
        # Generate glossary mappings
        print("Generating glossary mappings...")
        generate_glossary_mappings(db, org.id, proj.id, args.seed)
        print("Glossary mappings created")
        
        print("\n=== Synthetic Data Generation Complete ===")
        print(f"Organization: {org.name} (id={org.id})")
        print(f"Project: {proj.name} (id={proj.id})")
        print(f"WBS Nodes: {len(wbs_nodes)}")
        print(f"Field Events: {len(events)}")
        print(f"Demo credentials: supervisor@demo.com / supervisor123")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()