export interface ReferralTransaction{

    id:number;

    referrerId:string;

    referredUserId:string;

    paymentId:number;

    service:string;

    amount:number;

    commission:number;

    createdAt:string;
}