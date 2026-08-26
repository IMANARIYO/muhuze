import Container from "../../components/ui/Container";
import SectionTitle from "../../components/ui/SectionTitle";

import {
  ReferralCode,
  ReferralLink,
  ReferralStatistics,
  ReferralHistory,
  InviteFriends,
} from "../../components/referral";
import ReferralCommissionStatistics from "../../components/referral/ReferralCommissionStatistics";
import ReferralCommissionHistory from "../../components/referral/ReferralCommissionHistory";

export default function Referral() {
  return (
    <section className="py-16 bg-slate-50 min-h-screen">
      <Container>

        <SectionTitle
          title="Referral Program"
          subtitle="Invite your friends and earn rewards for every successful referral."
        />

        <ReferralCode />

        <ReferralLink />

        <ReferralStatistics />

        <ReferralHistory />

        <InviteFriends />
        <ReferralCommissionStatistics />

        <ReferralCommissionHistory />

      </Container>
    </section>
  );
}