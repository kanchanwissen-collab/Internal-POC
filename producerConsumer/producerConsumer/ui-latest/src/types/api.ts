
export interface ManualAction {
    _id: string;
    request_id: string;
    action_type: string;
    reason: string;
    action_at: string;
}

export interface Status {
    _id: string;
    batch_id: string;
    request_id: string;
    status: 'submitted' | 'queued' | 'expired' | 'running' | 'failed' | 'approved' | 'denied' | 'manual-action';
}

export interface ApiRequest {
    request_id: string;
    batch_id: string;
    sequence_no: string;
    vendor: string;
    status: Status;
    manual_actions: ManualAction[];
}

export interface ApiResponse {
    status: string;
    message: string;
    data: ApiRequest[];
}
