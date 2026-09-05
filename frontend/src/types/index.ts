export type UserRole =
  | 'SYSTEM_ADMIN'
  | 'CONTRACTOR_ADMIN'
  | 'PROJECT_CONTROLS'
  | 'DISCIPLINE_PLANNER'
  | 'SITE_SUPERVISOR'

export interface User {
  id: number
  email: string
  full_name: string
  role: UserRole
  organization_id: number
  discipline: string | null
  preferred_language: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Organization {
  id: number
  name: string
  slug: string
  description: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Project {
  id: number
  name: string
  code: string
  description: string | null
  organization_id: number
  location: string | null
  latitude: string | null
  longitude: string | null
  start_date: string | null
  end_date: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ScheduleActivity {
  id: number
  organization_id: number
  project_id: number
  activity_code: string
  activity_name: string
  discipline: string
  wbs: string
  planned_start: string
  planned_finish: string
  is_unplanned: boolean
  created_at: string
  external_schedule_id: number | null
  external_activity_id: string | null
  source_format: string | null
  actual_start?: string | null
  actual_finish?: string | null
}

export interface ProgressEvent {
  id: number
  organization_id: number
  project_id: number
  user_id: number | null
  raw_text: string
  activity_reference: string | null
  event_type: string
  event_date: string | null
  event_time: string | null
  discipline: string | null
  location: string | null
  equipment_tag: string | null
  source_type: string
  source_file: string | null
  session_id: string | null
  ingestion_source_id: number | null
  created_at: string
}

export interface ConfidenceResult {
  id: number
  progress_event_id: number
  proposed_activity_id: number | null
  confidence_score: number
  confidence_level: 'HIGH' | 'MEDIUM' | 'LOW'
  decision: 'AUTO_MATCH' | 'APPROVED' | 'CORRECTED' | 'REJECTED' | 'NEW_ACTIVITY_CREATED'
  score_gap: number | null
  exact_identifier_strength: number | null
  fuzzy_similarity: number | null
  semantic_similarity: number | null
  discipline_compatibility: number | null
  context_compatibility: number | null
  temporal_compatibility: number | null
  missing_information_penalty: number | null
  candidate_ambiguity_penalty: number | null
  created_at: string
}

export interface PlannerReview {
  id: number
  progress_event_id: number
  proposed_activity_id: number | null
  final_activity_id: number | null
  new_activity_id: number | null
  confidence_score: number
  confidence_level: 'HIGH' | 'MEDIUM' | 'LOW'
  status: 'PENDING' | 'APPROVED' | 'CORRECTED' | 'REJECTED' | 'NEW_ACTIVITY_CREATED'
  top_candidates_json: string | null
  score_breakdown_json: string | null
  matching_reasons_json: string | null
  reviewer_note: string | null
  created_at: string
  completed_at: string | null
}

export interface WBSNode {
  id: number
  project_id: number
  activity_code: string
  activity_name: string
  discipline: string
  wbs: string
  level: number
  parent_id: number | null
  planned_start: string
  planned_finish: string
  actual_start: string | null
  actual_finish: string | null
  is_unplanned: boolean
  is_milestone: boolean
  description_vector: unknown | null
  external_schedule_id: number | null
  external_activity_id: string | null
  source_format: string | null
  created_at: string
  updated_at: string
  children?: WBSNode[]
}

export interface EventWBSMatch {
  id: number
  progress_event_id: number
  wbs_node_id: number | null
  match_type: 'EXACT' | 'FUZZY' | 'SEMANTIC' | 'CONTEXTUAL' | 'NEW_ACTIVITY'
  confidence_score: number
  progress_contribution_pct: number | null
  score_breakdown_json: string | null
  created_at: string
}

export interface DelayReason {
  id: number
  project_id: number
  wbs_node_id: number | null
  category: 'WEATHER' | 'RESOURCE' | 'MATERIAL' | 'DESIGN' | 'PERMIT' | 'SUBCONTRACTOR' | 'EXTERNAL' | 'OTHER'
  description: string
  impact_days: number
  is_critical_path: boolean
  reported_by: number | null
  created_at: string
}

export interface ProductivityBenchmark {
  id: number
  organization_id: number
  project_id: number | null
  discipline: string
  activity_type: string
  unit: string
  planned_quantity: number | null
  actual_quantity: number | null
  planned_duration_days: number | null
  actual_duration_days: number | null
  productivity_rate: number | null
  sample_size: number
  period_start: string | null
  period_end: string | null
  created_at: string
  updated_at: string
}

export interface GlossaryMapping {
  id: number
  organization_id: number
  project_id: number | null
  source_term: string
  standardized_term: string
  discipline: string | null
  context: string | null
  created_by: number | null
  created_at: string
}

export interface AuditLog {
  id: number
  organization_id: number
  project_id: number | null
  user_id: number | null
  action: string
  entity_type: string
  entity_id: number | null
  old_values: unknown | null
  new_values: unknown | null
  ip_address: string | null
  user_agent: string | null
  created_at: string
}

export interface IngestionSource {
  id: number
  code: string
  name: string
  description: string | null
  is_active: boolean
  created_at: string
}

export interface MatchingResult {
  progress_event_id: number
  top_matches: Array<{
    activity_id: number
    activity_code: string
    activity_name: string
    confidence_score: number
    match_type: string
    reasons: string[]
  }>
  decision: 'AUTO_MATCH' | 'REVIEW' | 'NEW_ACTIVITY'
}