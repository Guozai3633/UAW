import {requestMeta,UawClient} from '../../lib/api/client';
import type {Schema} from '../../lib/api/types';
import {validate} from '../../lib/api/validation';

export type QualityView=Schema['QualityReviewView'];
export type Judgment=Schema['QualityJudgment'];
export type Feedback=Schema['QualityFeedback'];
export type FeedbackPin={run_id:string;run_revision:number;input_revision:number};
export interface QualityPort {
 list(cursor?:string,signal?:AbortSignal):Promise<Schema['QualityReviewPage']>;
 get(id:string,signal?:AbortSignal):Promise<QualityView>;
 save(view:QualityView,judgments:Judgment[],submit:boolean,signal?:AbortSignal):Promise<QualityView>;
 export(id:string,signal?:AbortSignal):Promise<Schema['QualityExport']>;
 feedback(runId:string,signal?:AbortSignal):Promise<Schema['QualityFeedbackPage']>;
 saveFeedback(pin:FeedbackPin,category:Feedback['category'],notes:string,original?:Feedback,signal?:AbortSignal):Promise<Feedback>;
}
export class HttpQualityPort implements QualityPort {
 constructor(private client:UawClient){}
 list(cursor?:string,signal?:AbortSignal){return this.client.call<Schema['QualityReviewPage']>('GET','/v1/quality/reviews','HttpQualityReviewsListResult',{cursor},undefined,undefined,signal);}
 get(id:string,signal?:AbortSignal){return this.client.call<QualityView>('GET',`/v1/quality/reviews/${encodeURIComponent(id)}`,'HttpQualityReviewsGetResult',{},undefined,undefined,signal);}
 save(view:QualityView,judgments:Judgment[],submit:boolean,signal?:AbortSignal){
  const request={review_id:view.id,packet_sha256:view.packet_sha256,judgments,...(submit?{human_attested:true}:{})};
  validate(submit?'QualityReviewsSubmitRequest':'QualityReviewsSaveRequest',request);
  const {review_id,...payload}=request;
  return this.client.call<QualityView>('POST',`/v1/quality/reviews/${encodeURIComponent(review_id)}/${submit?'submission':'draft'}`,submit?'HttpQualityReviewsSubmitResult':'HttpQualityReviewsSaveResult',{},payload,requestMeta(view.revision),signal);
 }
 export(id:string,signal?:AbortSignal){return this.client.call<Schema['QualityExport']>('GET',`/v1/quality/reviews/${encodeURIComponent(id)}/export`,'HttpQualityReviewsExportResult',{},undefined,undefined,signal);}
 feedback(runId:string,signal?:AbortSignal){return this.client.call<Schema['QualityFeedbackPage']>('GET',`/v1/runs/${encodeURIComponent(runId)}/feedback`,'HttpQualityFeedbackListResult',{},undefined,undefined,signal);}
 saveFeedback(pin:FeedbackPin,category:Feedback['category'],notes:string,original?:Feedback,signal?:AbortSignal){
  const payload={feedback_id:original?.id??`feedback-${crypto.randomUUID()}`,run_revision:original?.run_revision??pin.run_revision,input_revision:original?.input_revision??pin.input_revision,category,notes};
  validate('QualityFeedbackSaveRequest',{...payload,run_id:pin.run_id});
  return this.client.call<Feedback>('POST',`/v1/runs/${encodeURIComponent(pin.run_id)}/feedback`,'HttpQualityFeedbackSaveResult',{},payload,requestMeta(original?.revision??0),signal);
 }
}
