import { JobItem } from '../types';

export type ProgressCallback = (event: Partial<JobItem>) => void;

export class JobSSEClient {
  private eventSource: EventSource | null = null;
  private jobId: string;
  private onProgress: ProgressCallback;
  private onComplete: (data: any) => void;
  private onError: (err: any) => void;

  constructor(
    jobId: string,
    onProgress: ProgressCallback,
    onComplete: (data: any) => void,
    onError: (err: any) => void
  ) {
    self = this as any;
    this.jobId = jobId;
    this.onProgress = onProgress;
    this.onComplete = onComplete;
    this.onError = onError;
  }

  public connect(): void {
    const streamUrl = `/api/jobs/${this.jobId}/stream`;
    this.eventSource = new EventSource(streamUrl);

    this.eventSource.addEventListener('progress', (e: MessageEvent) => {
      try {
        const payload = JSON.parse(e.data);
        this.onProgress(payload);
      } catch (err) {
        console.error('Error parsing SSE progress payload:', err);
      }
    });

    this.eventSource.addEventListener('completed', (e: MessageEvent) => {
      try {
        const payload = JSON.parse(e.data);
        this.onProgress(payload);
        this.onComplete(payload);
      } catch (err) {
        console.error('Error parsing SSE completed payload:', err);
      }
      this.close();
    });

    this.eventSource.addEventListener('failed', (e: MessageEvent) => {
      try {
        const payload = JSON.parse(e.data);
        this.onProgress(payload);
        this.onError(payload);
      } catch (err) {
        console.error('Error parsing SSE failed payload:', err);
      }
      this.close();
    });

    this.eventSource.onerror = (err) => {
      this.onError(err);
      this.close();
    };
  }

  public close(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }
}
