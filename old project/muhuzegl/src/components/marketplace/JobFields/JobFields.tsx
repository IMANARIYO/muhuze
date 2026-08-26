import Input from "../../ui/Input";

interface Props {
  company: string;
  position: string;
  employmentType: string;
  salary: string;
  experience: string;
  applicationDeadline: string;

  onCompanyChange: (value: string) => void;
  onPositionChange: (value: string) => void;
  onEmploymentTypeChange: (value: string) => void;
  onSalaryChange: (value: string) => void;
  onExperienceChange: (value: string) => void;
  onApplicationDeadlineChange: (
    value: string
  ) => void;
}

export default function JobFields({
  company,
  position,
  employmentType,
  salary,
  experience,
  applicationDeadline,
  onCompanyChange,
  onPositionChange,
  onEmploymentTypeChange,
  onSalaryChange,
  onExperienceChange,
  onApplicationDeadlineChange,
}: Props) {
  return (
    <div className="space-y-6">

      <h3 className="text-xl font-bold">
        Job Information
      </h3>

      <Input
        label="Company"
        value={company}
        onChange={(e) =>
          onCompanyChange(e.target.value)
        }
      />

      <Input
        label="Position"
        value={position}
        onChange={(e) =>
          onPositionChange(e.target.value)
        }
      />

      <div>
        <label className="block mb-2 font-medium">
          Employment Type
        </label>

        <select
          value={employmentType}
          onChange={(e) =>
            onEmploymentTypeChange(
              e.target.value
            )
          }
          className="w-full rounded-xl border px-4 py-3"
        >
          <option value="">
            Select Type
          </option>

          <option value="full-time">
            Full Time
          </option>

          <option value="part-time">
            Part Time
          </option>

          <option value="contract">
            Contract
          </option>

          <option value="internship">
            Internship
          </option>

          <option value="remote">
            Remote
          </option>
        </select>
      </div>

      <Input
        label="Salary"
        value={salary}
        onChange={(e) =>
          onSalaryChange(e.target.value)
        }
      />

      <Input
        label="Experience Required"
        value={experience}
        onChange={(e) =>
          onExperienceChange(e.target.value)
        }
      />

      <Input
        label="Application Deadline"
        type="date"
        value={applicationDeadline}
        onChange={(e) =>
          onApplicationDeadlineChange(
            e.target.value
          )
        }
      />

    </div>
  );
}