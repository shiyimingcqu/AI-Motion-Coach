import { defineStore } from "pinia";
import {
  getErrorFrames,
  getPersonalReport,
  getReports,
  type ErrorFramesResponse,
  type PersonalReport,
  type ReportItem,
  type ReportQuery,
} from "@/api/reports";

type ReportsListResult = { items: ReportItem[]; total: number };

function serializeQuery(params?: ReportQuery): string {
  return JSON.stringify({
    date_from: params?.date_from ?? "",
    date_to: params?.date_to ?? "",
    exercise: params?.exercise ?? "",
  });
}

export const useReportsCacheStore = defineStore("reportsCache", {
  state: () => ({
    personalByKey: {} as Record<string, PersonalReport>,
    reportsByKey: {} as Record<string, ReportsListResult>,
    errorFramesByKey: {} as Record<string, ErrorFramesResponse>,
    inflight: new Map<string, Promise<unknown>>(),
  }),

  actions: {
    getPersonalCached(params?: ReportQuery) {
      return this.personalByKey[serializeQuery(params)];
    },

    getReportsCached(params?: ReportQuery) {
      return this.reportsByKey[serializeQuery(params)];
    },

    getErrorFramesCached(params?: ReportQuery) {
      return this.errorFramesByKey[serializeQuery(params)];
    },

    async dedupe<T>(key: string, factory: () => Promise<T>): Promise<T> {
      const existing = this.inflight.get(key);
      if (existing) return existing as Promise<T>;
      const promise = factory().finally(() => {
        this.inflight.delete(key);
      });
      this.inflight.set(key, promise);
      return promise;
    },

    async fetchPersonalReport(params?: ReportQuery, options?: { force?: boolean }) {
      const queryKey = serializeQuery(params);
      if (!options?.force && this.personalByKey[queryKey]) {
        return this.personalByKey[queryKey];
      }
      return this.dedupe(`personal:${queryKey}`, async () => {
        const data = await getPersonalReport(params);
        this.personalByKey[queryKey] = data;
        return data;
      });
    },

    async fetchReports(params?: ReportQuery, options?: { force?: boolean }) {
      const queryKey = serializeQuery(params);
      if (!options?.force && this.reportsByKey[queryKey]) {
        return this.reportsByKey[queryKey];
      }
      return this.dedupe(`reports:${queryKey}`, async () => {
        const data = await getReports(params);
        this.reportsByKey[queryKey] = data;
        return data;
      });
    },

    async fetchErrorFrames(params?: ReportQuery, options?: { force?: boolean }) {
      const queryKey = serializeQuery(params);
      if (!options?.force && this.errorFramesByKey[queryKey]) {
        return this.errorFramesByKey[queryKey];
      }
      return this.dedupe(`frames:${queryKey}`, async () => {
        const data = await getErrorFrames(params);
        this.errorFramesByKey[queryKey] = data;
        return data;
      });
    },

    prefetchAssessmentBundle(baseQuery: ReportQuery) {
      void this.fetchPersonalReport(baseQuery);
      void this.fetchErrorFrames(baseQuery);
    },

    prefetchExportBundle(baseQuery: ReportQuery) {
      void this.fetchPersonalReport(baseQuery);
      void this.fetchReports(baseQuery);
    },
  },
});

export function defaultRecentRangeQuery(): ReportQuery {
  const today = new Date();
  const from = new Date(today);
  from.setDate(from.getDate() - 6);
  return {
    date_from: from.toISOString().slice(0, 10),
    date_to: today.toISOString().slice(0, 10),
  };
}
