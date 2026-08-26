import Input from "../../components/ui/Input";

interface Props {
  fullName: string;
  email: string;
  phoneNumber: string;

  setFullName: (value: string) => void;
  setEmail: (value: string) => void;
  setPhoneNumber: (value: string) => void;
}

export default function CustomerInformation({
  fullName,
  email,
  phoneNumber,
  setFullName,
  setEmail,
  setPhoneNumber,
}: Props) {
  return (
    <div className="mt-10 max-w-2xl">

      <h2 className="text-2xl font-bold mb-6">
        CUSTOMER INFORMATION
      </h2>

      <div className="space-y-5">

        <Input
          label="Full Name"
          type="text"
          placeholder="Enter your full name"
          value={fullName}
          onChange={(e) =>
            setFullName(e.target.value)
          }
        />

        <Input
          label="Email Address"
          type="email"
          placeholder="Enter your email"
          value={email}
          onChange={(e) =>
            setEmail(e.target.value)
          }
        />

        <Input
          label="Phone Number"
          type="tel"
          placeholder="Enter your phone number"
          value={phoneNumber}
          onChange={(e) =>
            setPhoneNumber(e.target.value)
          }
        />

      </div>

    </div>
  );
}