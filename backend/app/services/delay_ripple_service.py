from typing import List, Dict, Set, Tuple, Optional
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.schedule import ScheduleActivity
from app.models.wbs_node import WBSNode
from app.models.xer import ScheduleRelationship
from app.models.delay_impact import DelayImpact, ImpactType
from app.models.progress import ProgressEvent
from collections import defaultdict, deque


class DelayRippleService:
    """Deterministic graph traversal for delay ripple computation."""

    RELATIONSHIP_TYPES = {"FS", "SS", "FF", "SF"}

    def __init__(self, db: Session):
        self.db = db

    def compute_delay_ripple(
        self,
        project_id: int,
        source_event_id: int,
        source_wbs_node_id: int,
        delay_days: int,
    ) -> List[DelayImpact]:
        """
        Compute delay ripple from a DELAY event approval.

        Args:
            project_id: Project ID
            source_event_id: ProgressEvent ID that triggered the delay
            source_wbs_node_id: WBSNode ID of the delayed activity
            delay_days: Number of days of delay

        Returns:
            List of created DelayImpact records
        """
        # Get all schedule relationships for this project
        relationships = self._get_project_relationships(project_id)

        # Build adjacency list for successor traversal
        successors = self._build_successor_map(relationships)

        # Get all activities for float computation
        activities = self._get_project_activities(project_id)
        activity_map = {a.id: a for a in activities}

        # Compute critical path and float for all activities
        critical_path_set, float_map = self._compute_critical_path_and_float(
            project_id, activities, relationships
        )

        # BFS traversal from delayed activity
        impacts = self._traverse_successors(
            project_id=project_id,
            source_event_id=source_event_id,
            source_wbs_node_id=source_wbs_node_id,
            delay_days=delay_days,
            successors=successors,
            activity_map=activity_map,
            critical_path_set=critical_path_set,
            float_map=float_map,
        )

        # Persist impacts
        for impact in impacts:
            self.db.add(impact)
        self.db.commit()

        return impacts

    def _get_project_relationships(self, project_id: int) -> List[ScheduleRelationship]:
        """Get all schedule relationships for a project."""
        return self.db.query(ScheduleRelationship).join(
            ScheduleActivity, ScheduleRelationship.predecessor_activity_id == ScheduleActivity.id
        ).filter(ScheduleActivity.project_id == project_id).all()

    def _get_project_activities(self, project_id: int) -> List[ScheduleActivity]:
        """Get all schedule activities for a project."""
        return self.db.query(ScheduleActivity).filter(
            ScheduleActivity.project_id == project_id
        ).all()

    def _build_successor_map(
        self, relationships: List[ScheduleRelationship]
    ) -> Dict[int, List[Tuple[int, str, int]]]:
        """Build map of activity_id -> list of (successor_id, relationship_type, lag_days)."""
        successors = defaultdict(list)
        for rel in relationships:
            lag_days = rel.lag if rel.lag_unit == "days" else rel.lag * 8  # Convert hours to days if needed
            successors[rel.predecessor_activity_id].append(
                (rel.successor_activity_id, rel.relationship_type, lag_days)
            )
        return successors

    def _compute_critical_path_and_float(
        self,
        project_id: int,
        activities: List[ScheduleActivity],
        relationships: List[ScheduleRelationship],
    ) -> Tuple[Set[int], Dict[int, int]]:
        """
        Compute critical path using CPM (Critical Path Method) and schedule margin.
        Returns (critical_path_activity_ids, schedule_margin_map).
        
        Schedule margin = planned_start - early_start (network-driven).
        This represents how much delay a successor can absorb before its planned start is affected.
        """
        if not activities:
            return set(), {}

        activity_map = {a.id: a for a in activities}
        pred_map = defaultdict(list)
        succ_map = defaultdict(list)

        for rel in relationships:
            pred_map[rel.successor_activity_id].append(rel)
            succ_map[rel.predecessor_activity_id].append(rel)

        # Forward pass - Early Start / Early Finish
        # Compute purely from network logic
        early_start = {}
        early_finish = {}

        # Topological sort
        in_degree = defaultdict(int)
        for rel in relationships:
            in_degree[rel.successor_activity_id] += 1

        # Start with activities that have no predecessors
        queue = deque([a.id for a in activities if in_degree[a.id] == 0])

        # Initialize early times for activities with no predecessors = their planned dates
        for act in activities:
            if in_degree[act.id] == 0:
                early_start[act.id] = act.planned_start
                early_finish[act.id] = act.planned_finish
            else:
                early_start[act.id] = date(1900, 1, 1)  # Will be updated by predecessors
                early_finish[act.id] = date(1900, 1, 1)

        topo_order = []
        while queue:
            act_id = queue.popleft()
            topo_order.append(act_id)

            for rel in succ_map.get(act_id, []):
                succ_id = rel.successor_activity_id
                lag = timedelta(days=rel.lag) if rel.lag_unit == "days" else timedelta(hours=rel.lag)

                # Compute early start based on relationship type
                pred_es = early_start.get(act_id, activity_map[act_id].planned_start)
                pred_ef = early_finish.get(act_id, activity_map[act_id].planned_finish)

                if rel.relationship_type == "FS":
                    new_es = pred_ef + lag
                elif rel.relationship_type == "SS":
                    new_es = pred_es + lag
                elif rel.relationship_type == "FF":
                    new_es = pred_ef + lag - (activity_map[succ_id].planned_finish - activity_map[succ_id].planned_start)
                elif rel.relationship_type == "SF":
                    new_es = pred_es + lag - (activity_map[succ_id].planned_finish - activity_map[succ_id].planned_start)
                else:
                    new_es = early_start.get(succ_id, date(1900, 1, 1))

                # Take the maximum of all predecessor constraints
                if new_es > early_start.get(succ_id, date(1900, 1, 1)):
                    early_start[succ_id] = new_es
                    early_finish[succ_id] = new_es + (activity_map[succ_id].planned_finish - activity_map[succ_id].planned_start)

                in_degree[succ_id] -= 1
                if in_degree[succ_id] == 0:
                    queue.append(succ_id)

        # Backward pass - Late Start / Late Finish for critical path detection
        late_start = {}
        late_finish = {}

        # Project finish = max early finish (critical path length)
        project_finish = max(early_finish.values()) if early_finish else date.today()

        # Initialize late times for activities with no successors = project_finish
        for act in activities:
            if not succ_map.get(act.id):
                late_finish[act.id] = project_finish
                late_start[act.id] = project_finish - (act.planned_finish - act.planned_start)
            else:
                late_finish[act.id] = date(9999, 12, 31)
                late_start[act.id] = date(9999, 12, 31)

        # Process in reverse topological order
        for act_id in reversed(topo_order):
            act = activity_map[act_id]
            duration = act.planned_finish - act.planned_start

            for rel in succ_map.get(act_id, []):
                succ_id = rel.successor_activity_id
                lag = timedelta(days=rel.lag) if rel.lag_unit == "days" else timedelta(hours=rel.lag)

                # Compute late finish based on relationship type
                if rel.relationship_type == "FS":
                    new_lf = late_start[succ_id] - lag
                elif rel.relationship_type == "SS":
                    new_lf = late_start[succ_id] - lag + duration
                elif rel.relationship_type == "FF":
                    new_lf = late_finish[succ_id] - lag
                elif rel.relationship_type == "SF":
                    new_lf = late_finish[succ_id] - lag + duration
                else:
                    new_lf = late_finish[succ_id]

                # Take the minimum of all successor constraints
                if new_lf < late_finish[act_id]:
                    late_finish[act_id] = new_lf
                    late_start[act_id] = new_lf - duration

        # Compute schedule margin (planned_start - early_start) and critical path
        schedule_margin = {}
        critical_path = set()

        for act in activities:
            # Total float (CPM) - for critical path detection
            total_float = (late_start[act.id] - early_start[act.id]).days
            if total_float <= 0:
                critical_path.add(act.id)
            
            # Schedule margin = planned_start - early_start
            # This is how much the activity can be delayed from its network-driven
            # early start before it affects its planned start date
            margin = (act.planned_start - early_start[act.id]).days
            schedule_margin[act.id] = max(0, margin)

        return critical_path, schedule_margin

    def _traverse_successors(
        self,
        project_id: int,
        source_event_id: int,
        source_wbs_node_id: int,
        delay_days: int,
        successors: Dict[int, List[Tuple[int, str, int]]],
        activity_map: Dict[int, ScheduleActivity],
        critical_path_set: Set[int],
        float_map: Dict[int, int],
    ) -> List[DelayImpact]:
        """BFS traversal to compute propagated delays."""
        impacts = []
        visited = set()
        queue = deque()

        # Find the ScheduleActivity ID corresponding to the source_wbs_node_id
        source_activity = self.db.query(ScheduleActivity).filter(
            ScheduleActivity.project_id == project_id,
            ScheduleActivity.activity_code == self.db.query(WBSNode).filter(WBSNode.id == source_wbs_node_id).first().activity_code
        ).first()

        if not source_activity:
            return impacts

        # Start with direct successors of the delayed activity
        queue.append((source_activity.id, delay_days, 0, "DIRECT"))  # (activity_id, delay, depth, impact_type)

        while queue:
            current_id, current_delay, depth, impact_type = queue.popleft()

            if current_id in visited:
                continue
            visited.add(current_id)

            for succ_id, rel_type, lag_days in successors.get(current_id, []):
                if succ_id in visited:
                    continue

                # Compute propagated delay based on relationship type
                propagated_delay = self._compute_propagated_delay(
                    current_delay, rel_type, lag_days,
                    activity_map.get(current_id), activity_map.get(succ_id)
                )

                if propagated_delay <= 0:
                    continue

                # Determine impact type
                if depth == 0:
                    impact_type = ImpactType.DIRECT
                elif succ_id in critical_path_set:
                    impact_type = ImpactType.CRITICAL_PATH
                elif float_map.get(succ_id, 0) < propagated_delay:
                    impact_type = ImpactType.FLOAT_CONSUMED
                else:
                    impact_type = ImpactType.PROPAGATED

                # Calculate float consumption
                available_float = float_map.get(succ_id, 0)
                float_consumed = min(propagated_delay, available_float)
                remaining_float = available_float - float_consumed

                # Check critical path exposure
                is_critical = succ_id in critical_path_set
                # Critical path exposure: delay meets or exceeds available schedule margin
                # (not just CPM critical path - we care about baseline schedule impact)
                critical_exposure = propagated_delay >= available_float

                # Get WBS node for impacted activity
                succ_activity = activity_map.get(succ_id)
                impacted_wbs_node = None
                if succ_activity:
                    impacted_wbs_node = self.db.query(WBSNode).filter(
                        WBSNode.project_id == project_id,
                        WBSNode.activity_code == succ_activity.activity_code
                    ).first()

                if not impacted_wbs_node:
                    continue

                impact = DelayImpact(
                    project_id=project_id,
                    source_event_id=source_event_id,
                    source_wbs_node_id=source_wbs_node_id,
                    impacted_wbs_node_id=impacted_wbs_node.id,
                    impact_type=impact_type,
                    relationship_type=rel_type,
                    lag_days=lag_days,
                    original_delay_days=delay_days,
                    propagated_delay_days=propagated_delay,
                    float_consumed_days=float_consumed,
                    remaining_float_days=remaining_float,
                    is_critical_path=is_critical,
                    critical_path_exposure=critical_exposure,
                    path_depth=depth + 1,
                )
                impacts.append(impact)

                # Continue traversal
                queue.append((succ_id, propagated_delay, depth + 1, impact_type.value))

        return impacts

    def _compute_propagated_delay(
        self,
        current_delay: int,
        relationship_type: str,
        lag_days: int,
        pred_activity: Optional[ScheduleActivity],
        succ_activity: Optional[ScheduleActivity],
    ) -> int:
        """
        Compute propagated delay based on relationship type.
        
        FS (Finish-to-Start): Successor starts after predecessor finishes + lag
        SS (Start-to-Start): Successor starts after predecessor starts + lag
        FF (Finish-to-Finish): Successor finishes after predecessor finishes + lag
        SF (Start-to-Finish): Successor finishes after predecessor starts + lag
        """
        if not pred_activity or not succ_activity:
            return current_delay

        pred_duration = (pred_activity.planned_finish - pred_activity.planned_start).days
        succ_duration = (succ_activity.planned_finish - succ_activity.planned_start).days

        if relationship_type == "FS":
            # Delay propagates fully if no float
            return current_delay
        elif relationship_type == "SS":
            # Delay propagates fully if no float
            return current_delay
        elif relationship_type == "FF":
            # Delay propagates fully if no float
            return current_delay
        elif relationship_type == "SF":
            # SF is unusual but delay can propagate
            return current_delay
        else:
            return current_delay

    def get_delay_impacts_for_event(self, event_id: int) -> List[DelayImpact]:
        """Get all delay impacts for a specific progress event."""
        return self.db.query(DelayImpact).filter(
            DelayImpact.source_event_id == event_id
        ).order_by(DelayImpact.path_depth, DelayImpact.propagated_delay_days.desc()).all()

    def get_delay_impacts_for_activity(self, project_id: int, wbs_node_id: int) -> List[DelayImpact]:
        """Get all delay impacts affecting a specific activity."""
        return self.db.query(DelayImpact).filter(
            DelayImpact.project_id == project_id,
            DelayImpact.impacted_wbs_node_id == wbs_node_id
        ).order_by(DelayImpact.computed_at.desc()).all()

    def get_critical_path_impacts(self, project_id: int) -> List[DelayImpact]:
        """Get all critical path delay impacts for a project."""
        return self.db.query(DelayImpact).filter(
            DelayImpact.project_id == project_id,
            DelayImpact.is_critical_path == True
        ).order_by(DelayImpact.propagated_delay_days.desc()).all()