import EditProfileForm from "../../components/profile/EditProfileForm/EditProfileForm";
import Container from "../../components/ui/Container";
import SectionTitle from "../../components/ui/SectionTitle";

export default function EditProfile() {
  return (
    <section className="py-12">
      <Container>
        <SectionTitle
          title="Edit Profile"
          subtitle="Update your personal information."
        />

        <div className="mt-8">
          <EditProfileForm />
        </div>
      </Container>
    </section>
  );
}