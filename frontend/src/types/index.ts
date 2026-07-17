export interface User {
  id: number;
  email: string;
  username: string;
  full_name: string | null;
  profile_picture: string | null;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface Resume {
  id: number;
  filename: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  extracted_data: ResumeData | null;
  created_at: string;
}

export interface ResumeData {
  name: string;
  email: string;
  phone: string;
  location: string;
  skills: string[];
  education: string[];
  experience: string[];
  projects: string[];
  certificates: string[];
  languages: string[];
  raw_text: string;
}

export interface ATSDetails {
  overall: number;
  formatting: number;
  keywords: number;
  experience: number;
  education: number;
  skills: number;
}

export interface Suggestion {
  type: string;
  severity: "high" | "medium" | "low";
  title: string;
  description: string;
  category: string;
}

export interface JobMatch {
  similarity_score: number;
  recommended_roles: { title: string; match: number }[];
}

export interface Analysis {
  id: number;
  resume_id: number;
  ats_score: number | null;
  ats_details: ATSDetails | null;
  missing_skills: string[];
  matched_skills: string[];
  partial_skills: string[];
  match_percentage: number;
  suggestions: Suggestion[];
  job_match: JobMatch | null;
  job_description: string | null;
  status: string;
  created_at: string;
  resume?: Resume;
}

export interface HistoryResponse {
  analyses: Analysis[];
  total: number;
  page: number;
  per_page: number;
}

export interface AnalyticsData {
  total_analyses: number;
  average_ats_score: number;
  most_common_skills: { skill: string; count: number }[];
  weekly_activity: { date: string; count: number }[];
  score_distribution: {
    excellent: number;
    good: number;
    average: number;
    poor: number;
  };
}

export interface ChangeDetail {
  original: string;
  corrected: string;
}

export interface CorrectionResult {
  corrected_pdf: string | null;
  corrected_docx: string | null;
  changes: ChangeDetail[];
  total_lines: number;
  changed_lines: number;
  message: string;
}
