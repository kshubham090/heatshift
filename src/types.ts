export interface Task {
  id: string;
  title: string;
  durationMinutes: number;
  earliestStart: string;
  latestEnd: string;
  baselineStart: string;
  locked: boolean;
}
export interface PlanRequest {
  date: string;
  location: { name: string; latitude: number; longitude: number };
  shiftStart: string;
  shiftEnd: string;
  breaks: { start: string; end: string }[];
  thresholdC: number;
  tasks: Task[];
}
export interface Weather {
  source: string;
  fetchedAt: string;
  mode: "live" | "saved";
  date: string;
  timezone: string;
  latitude: number;
  longitude: number;
  gridLatitude: number;
  gridLongitude: number;
  hours: {
    time: string;
    temperatureC: number;
    apparentTemperatureC: number;
    precipitationProbability: number | null;
  }[];
  attribution: string;
  sourceUrl: string;
  warnings: string[];
}
export interface ScheduleItem {
  taskId: string;
  title: string;
  start: string;
  end: string;
  locked: boolean;
  meanApparentTemperatureC: number;
}
export interface PlanResult {
  status: "improved" | "unchanged" | "planned" | "infeasible";
  schedule: ScheduleItem[];
  baselineSchedule: ScheduleItem[];
  baselineValid: boolean;
  metrics: {
    workMinutes: number;
    baselineMeanApparentTemperatureC: number | null;
    proposedMeanApparentTemperatureC: number | null;
    deltaC: number | null;
    baselineHotMinutes: number | null;
    proposedHotMinutes: number | null;
    thresholdC: number;
  };
  explanation: string;
  violations: string[];
  constraintChecks: { label: string; passed: boolean }[];
  weather: Weather;
  request: PlanRequest;
}
export interface Health {
  status: string;
  agent: { available: boolean; provider: string; model: string };
  version: string;
}
export interface AgentResponse {
  message: string;
  proposedPlan: PlanRequest | null;
  result: PlanResult | null;
  trace: { tool: string; status: "complete" | "error"; summary: string }[];
  provider: string;
  model: string;
  requiresApproval: boolean;
}
