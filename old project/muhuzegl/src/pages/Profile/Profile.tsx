import Container from "../../components/ui/Container";
import SectionTitle from "../../components/ui/SectionTitle";

import ProfileHeader from "../../components/profile/ProfileHeader/ProfileHeader";
import ProfileCompletion from "../../components/profile/ProfileCompletion/ProfileCompletion";
import ProfileInfo from "../../components/profile/ProfileInfo/ProfileInfo";
import ProfileActions from "../../components/profile/ProfileActions/ProfileActions";
import VerificationStatus from "../../components/profile/VerificationStatus/VerificationStatus";

export default function Profile() {
  return (
    <section className="py-12">
      <Container>

        <SectionTitle
          title="My Profile"
          subtitle="Manage your MUHUZE account."
        />

        {/* PROFILE SECTIONS */}

        <div className="mt-10 space-y-8">

          <ProfileHeader />

          <ProfileCompletion />
          <VerificationStatus />
          <ProfileInfo />

          <ProfileActions />

        </div>

      </Container>
    </section>
  );
}