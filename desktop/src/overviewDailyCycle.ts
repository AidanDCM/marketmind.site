import type {
  ApprovalRecord,
  DailyReport,
  ExperimentTrendSummary,
  OperatorHealthPanel,
  OperatorReadiness,
} from "./api/client";
import type { TrendDayOption } from "./components/overviewPreferences";

export type OverviewCycleData = [
  DailyReport,
  ApprovalRecord[],
  OperatorHealthPanel,
  OperatorReadiness,
  ExperimentTrendSummary,
];

export async function runOverviewDailyCycle(options: {
  date: string;
  trendDays: TrendDayOption;
  attentionOnly: boolean;
  runCycle: (date: string) => Promise<unknown>;
  fetchOverviewData: (
    date: string,
    trendDays: TrendDayOption,
    attentionOnly: boolean,
  ) => Promise<OverviewCycleData>;
  onCycleComplete?: () => void;
}): Promise<OverviewCycleData> {
  await options.runCycle(options.date);
  const data = await options.fetchOverviewData(
    options.date,
    options.trendDays,
    options.attentionOnly,
  );
  options.onCycleComplete?.();
  return data;
}
