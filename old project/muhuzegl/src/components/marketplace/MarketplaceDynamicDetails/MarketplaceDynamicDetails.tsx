import type { JobData, ProductData, RentalData, ServiceData } from "../../../types/marketplaceForm";
import type { MarketplaceItem } from "../../../types/marketplaceItem";

interface Props {
  item: MarketplaceItem;
}

export default function MarketplaceDynamicDetails({
  item,
}: Props) {
  return (
    <section className="mt-12">
      <h2 className="text-2xl font-bold mb-6">
        Listing Details
      </h2>

      {/* Dynamic Details will go here */}
      {item.marketplaceItemType === "product" && (() => {
  const details = item.details as ProductData;

  return (
    <div className="grid md:grid-cols-2 gap-6">

      <div>
        <h3 className="font-semibold">Brand</h3>
        <p>{details.brand}</p>
      </div>

      <div>
        <h3 className="font-semibold">Model</h3>
        <p>{details.model}</p>
      </div>

      <div>
        <h3 className="font-semibold">Condition</h3>
        <p>{details.condition}</p>
      </div>

      <div>
        <h3 className="font-semibold">Quantity</h3>
        <p>{details.quantity}</p>
      </div>

      <div>
        <h3 className="font-semibold">Warranty</h3>
        <p>{details.warranty}</p>
      </div>

    </div>
  );
})()}
    
{item.marketplaceItemType === "rental" &&
  (() => {
    const details = item.details as RentalData;

    return (
      <div className="grid md:grid-cols-2 gap-6">

        <div>
          <h3 className="font-semibold">Property Type</h3>
          <p>{details.propertyType}</p>
        </div>

        <div>
          <h3 className="font-semibold">Bedrooms</h3>
          <p>{details.bedrooms}</p>
        </div>

        <div>
          <h3 className="font-semibold">Bathrooms</h3>
          <p>{details.bathrooms}</p>
        </div>

        <div>
          <h3 className="font-semibold">Parking</h3>
          <p>{details.parking}</p>
        </div>

        <div>
          <h3 className="font-semibold">Furnished</h3>
          <p>{details.furnished ? "Yes" : "No"}</p>
        </div>

        <div>
          <h3 className="font-semibold">Rental Period</h3>
          <p>{details.rentalPeriod}</p>
        </div>

      </div>
    );
  })()}
  {/* Service */}
{item.marketplaceItemType === "service" &&
  (() => {
    const details = item.details as ServiceData;

    return (
      <div className="grid md:grid-cols-2 gap-6">

        <div>
          <h3 className="font-semibold">
            Service Category
          </h3>
          <p>{details.serviceCategory}</p>
        </div>

        <div>
          <h3 className="font-semibold">
            Experience
          </h3>
          <p>{details.experience}</p>
        </div>

        <div>
          <h3 className="font-semibold">
            Availability
          </h3>
          <p>{details.availability}</p>
        </div>

        <div>
          <h3 className="font-semibold">
            Service Area
          </h3>
          <p>{details.serviceArea}</p>
        </div>

        <div>
          <h3 className="font-semibold">
            Pricing Type
          </h3>
          <p>{details.pricingType}</p>
        </div>

      </div>
    );
  })()}
  {/* Job */}
{item.marketplaceItemType === "job" &&
  (() => {
    const details = item.details as JobData;

    return (
      <div className="grid md:grid-cols-2 gap-6">

        <div>
          <h3 className="font-semibold">
            Company
          </h3>
          <p>{details.company}</p>
        </div>

        <div>
          <h3 className="font-semibold">
            Position
          </h3>
          <p>{details.position}</p>
        </div>

        <div>
          <h3 className="font-semibold">
            Employment Type
          </h3>
          <p>{details.employmentType}</p>
        </div>

        <div>
          <h3 className="font-semibold">
            Salary
          </h3>
          <p>{details.salary}</p>
        </div>

        <div>
          <h3 className="font-semibold">
            Experience
          </h3>
          <p>{details.experience}</p>
        </div>

        <div>
          <h3 className="font-semibold">
            Education Level
          </h3>
          <p>{details.educationLevel}</p>
        </div>

        <div>
          <h3 className="font-semibold">
            Skills Required
          </h3>
          <p>{details.skillsRequired}</p>
        </div>

        <div>
          <h3 className="font-semibold">
            Recruiter Contact
          </h3>
          <p>{details.recruiterContact}</p>
        </div>

        <div>
          <h3 className="font-semibold">
            Application Deadline
          </h3>
          <p>{details.applicationDeadline}</p>
        </div>

      </div>
    );
  })()}
  </section>
  );
}