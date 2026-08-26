import {
  useEffect,
  useState,
} from "react";

import {
  useNavigate,
  useParams,
} from "react-router-dom";

import Container from "../../components/ui/Container";
import SectionTitle from "../../components/ui/SectionTitle";
import Button from "../../components/ui/Button";
import { useToast } from "../../components/ui/Toast";

import MarketplaceTypeSelector from "../../components/marketplace/MarketplaceTypeSelector";
import BasicInformation from "../../components/marketplace/BasicInformation";
import ImageUploader from "../../components/marketplace/ImageUploader";
import ProductFields from "../../components/marketplace/ProductFields";
import RentalFields from "../../components/marketplace/RentalFields";
import ServiceFields from "../../components/marketplace/ServiceFields";
import JobFields from "../../components/marketplace/JobFields";

import { useMarketplace } from "../../context/MarketplaceContext";
import { useAuth } from "../../context/AuthContext";

import {
  getProvinceById,
  getDistrictsByProvinceId,
} from "../../data/location/rwanda";

import type {
  CreateMarketplaceItem,
  MarketplaceItemType,
} from "../../types/marketplaceItem";

import type {
  BasicInfo,
  ProductData,
  RentalData,
  ServiceData,
  JobData,
} from "../../types/marketplaceForm";

export default function UploadMarketplaceItem() {
  const navigate = useNavigate();
  const { id } = useParams();

  const isEditing = Boolean(id);

  const {
    createItem,
    updateItem,
    getItemById,
  } = useMarketplace();

  const { currentUser } = useAuth();
  const { showToast } = useToast();

  const [
    marketplaceType,
    setMarketplaceType,
  ] = useState<MarketplaceItemType>(
    "product"
  );

  const [basicInfo, setBasicInfo] =
    useState<BasicInfo>({
      title: "",
      description: "",
      category: "",
      subCategory: "",
      price: "",
      location: "",
      images: [],
    });

  /*
   * Structured location state.
   *
   * We keep the existing location string
   * for compatibility with the current
   * MarketplaceItem type.
   */
  const [province, setProvince] =
    useState("");

  const [district, setDistrict] =
    useState("");

  const [existingImages, setExistingImages] =
    useState<string[]>([]);

  const [newImages, setNewImages] =
    useState<File[]>([]);

  const [productData, setProductData] =
    useState<ProductData>({
      brand: "",
      model: "",
      condition: "",
      quantity: "",
      warranty: "",
    });

  const [rentalData, setRentalData] =
  useState<RentalData>({
    rentalPeriod: "",
    condition: "",
    quantity: "",
    securityDeposit: "",
    availability: "",

    propertyType: "",
    bedrooms: "",
    bathrooms: "",
    parking: "",
    furnished: false,

    vehicleType: "",
    make: "",
    model: "",
    year: "",
    transmission: "",
    seats: "",

    equipmentType: "",
    eventType: "",
  });

  const [serviceData, setServiceData] =
    useState<ServiceData>({
      serviceCategory: "",
      experience: "",
      availability: "",
      serviceArea: "",
      pricingType: "",
    });

  const [jobData, setJobData] =
    useState<JobData>({
      company: "",
      position: "",
      employmentType: "",
      salary: "",
      experience: "",
      educationLevel: "",
      skillsRequired: "",
      recruiterContact: "",
      applicationDeadline: "",
    });

  /*
   * Convert the selected province/district
   * into the existing location string.
   *
   * Example:
   * Rwanda, City of Kigali, Nyarugenge
   */
  function buildLocationString(
    provinceId: string,
    districtId: string
  ) {
    const provinceData =
      getProvinceById(provinceId);

    const districtData =
      getDistrictsByProvinceId(
        provinceId
      ).find(
        (item) =>
          item.id === districtId
      );

    const parts = [
      "Rwanda",
      provinceData?.name,
      districtData?.name,
    ].filter(Boolean);

    return parts.join(", ");
  }

  /*
   * Update location whenever
   * province changes.
   */
  function handleProvinceChange(
    value: string
  ) {
    setProvince(value);

    setDistrict("");

    setBasicInfo((current) => ({
      ...current,
      location: buildLocationString(
        value,
        ""
      ),
    }));
  }

  /*
   * Update location whenever
   * district changes.
   */
  function handleDistrictChange(
    value: string
  ) {
    setDistrict(value);

    setBasicInfo((current) => ({
      ...current,
      location: buildLocationString(
        province,
        value
      ),
    }));
  }

  /*
   * Load existing listing in edit mode.
   */
  useEffect(() => {
    async function loadItem() {
      if (!id) {
        return;
      }

      try {
        const item =
          await getItemById(id);

        setMarketplaceType(
          item.marketplaceItemType
        );

        setBasicInfo({
          title: item.title,
          description:
            item.description,
          category: item.category,
          subCategory:
            item.subCategory,
          price:
            item.price.toString(),
          location:
            item.location,
          images: [],
        });

        setExistingImages(
          item.images
        );

        /*
         * Restore province/district
         * from the new location string.
         *
         * Expected format:
         * Rwanda, Province Name, District Name
         */
        const locationParts =
          item.location
            ?.split(",")
            .map((part) =>
              part.trim()
            ) ?? [];

        if (
          locationParts.length >= 3
        ) {
          const savedProvinceName =
            locationParts[1];

          const savedDistrictName =
            locationParts[2];

          const savedProvince =
            (
              await import(
                "../../data/location/rwanda"
              )
            ).rwandaProvinces.find(
              (provinceItem) =>
                provinceItem.name ===
                savedProvinceName
            );

          if (savedProvince) {
            setProvince(
              savedProvince.id
            );

            const savedDistrict =
              savedProvince.districts.find(
                (districtItem) =>
                  districtItem.name ===
                  savedDistrictName
              );

            if (savedDistrict) {
              setDistrict(
                savedDistrict.id
              );
            }
          }
        }

        if (
          item.marketplaceItemType ===
          "product"
        ) {
          setProductData(
            item.details as ProductData
          );
        }

        if (
          item.marketplaceItemType ===
          "rental"
        ) {
          setRentalData(
            item.details as RentalData
          );
        }

        if (
          item.marketplaceItemType ===
          "service"
        ) {
          setServiceData(
            item.details as ServiceData
          );
        }

        if (
          item.marketplaceItemType ===
          "job"
        ) {
          setJobData(
            item.details as JobData
          );
        }
      } catch (error) {
        console.error(
          "Failed to load listing:",
          error
        );

        showToast(
          "Failed to load listing.",
          "error"
        );
      }
    }

    loadItem();
  }, [
    id,
    getItemById,
    showToast,
  ]);

  async function handlePublish() {
    if (!currentUser) {
      showToast(
        "Please login first.",
        "warning"
      );
      return;
    }

    if (
      !basicInfo.title ||
      !basicInfo.category ||
      !basicInfo.subCategory ||
      !basicInfo.price
    ) {
      showToast(
        "Please complete the required fields.",
        "warning"
      );
      return;
    }

    if (!province || !district) {
      showToast(
        "Please select your province and district.",
        "warning"
      );
      return;
    }

    let details:
      | ProductData
      | RentalData
      | ServiceData
      | JobData;

    switch (marketplaceType) {
      case "product":
        details = productData;
        break;

      case "rental":
        details = rentalData;
        break;

      case "service":
        details = serviceData;
        break;

      case "job":
        details = jobData;
        break;
    }

    const newItem:
      CreateMarketplaceItem = {
      sellerId: currentUser._id,

      title:
        basicInfo.title,

      description:
        basicInfo.description,

      marketplaceItemType:
        marketplaceType,

      category:
        basicInfo.category,

      subCategory:
        basicInfo.subCategory,

      images: newImages,

      price:
        Number(basicInfo.price),

      currency: "RWF",

      location:
        basicInfo.location,

      verified: false,

      featured: false,

      rating: 0,

      reviews: 0,

      status: "published",

      details,

      createdAt:
        new Date().toISOString(),

      updatedAt:
        new Date().toISOString(),
    };

    if (
      isEditing &&
      id
    ) {
      await updateItem({
        _id: id,

        sellerId:
          currentUser._id,

        title:
          basicInfo.title,

        description:
          basicInfo.description,

        marketplaceItemType:
          marketplaceType,

        category:
          basicInfo.category,

        subCategory:
          basicInfo.subCategory,

        images:
          existingImages,

        newImages,

        price:
          Number(
            basicInfo.price
          ),

        currency: "RWF",

        location:
          basicInfo.location,

        verified: false,

        featured: false,

        rating: 0,

        reviews: 0,

        status: "published",

        details,

        updatedAt:
          new Date().toISOString(),
      });

      showToast(
        "Marketplace item updated successfully!",
        "success"
      );
    } else {
      await createItem(
        newItem
      );

      showToast(
        "Marketplace item published successfully!",
        "success"
      );
    }

    navigate(
      "/my-listings"
    );
  }

  return (
    <section className="py-16">
      <Container>

        <SectionTitle
          title={
            isEditing
              ? "Edit Marketplace Item"
              : "Publish Marketplace Item"
          }
          subtitle={
            isEditing
              ? "Update your marketplace listing."
              : "Create a new marketplace listing."
          }
        />

        {/* Marketplace Type */}

        <MarketplaceTypeSelector
          value={
            marketplaceType
          }
          onChange={(
            value
          ) => {
            setMarketplaceType(
              value
            );

            /*
             * Reset category and
             * subcategory when the
             * marketplace type changes.
             */
            setBasicInfo(
              (current) => ({
                ...current,
                category: "",
                subCategory: "",
              })
            );
          }}
        />

        {/* Basic Information */}

        <BasicInformation
          marketplaceType={
            marketplaceType
          }

          title={
            basicInfo.title
          }

          description={
            basicInfo.description
          }

          category={
            basicInfo.category
          }

          subCategory={
            basicInfo.subCategory
          }

          price={
            basicInfo.price
          }

          location={
            basicInfo.location
          }

          province={
            province
          }

          district={
            district
          }

          onTitleChange={(
            value
          ) =>
            setBasicInfo(
              (current) => ({
                ...current,
                title: value,
              })
            )
          }

          onDescriptionChange={(
            value
          ) =>
            setBasicInfo(
              (current) => ({
                ...current,
                description:
                  value,
              })
            )
          }

          onCategoryChange={(
            value
          ) =>
            setBasicInfo(
              (current) => ({
                ...current,
                category:
                  value,
                subCategory:
                  "",
              })
            )
          }

          onSubCategoryChange={(
            value
          ) =>
            setBasicInfo(
              (current) => ({
                ...current,
                subCategory:
                  value,
              })
            )
          }

          onPriceChange={(
            value
          ) =>
            setBasicInfo(
              (current) => ({
                ...current,
                price: value,
              })
            )
          }

          onLocationChange={(
            value
          ) =>
            setBasicInfo(
              (current) => ({
                ...current,
                location:
                  value,
              })
            )
          }

          onProvinceChange={
            handleProvinceChange
          }

          onDistrictChange={
            handleDistrictChange
          }
        />

        {/* Images */}

        <ImageUploader
          existingImages={
            existingImages
          }
          newImages={
            newImages
          }
          onExistingImagesChange={
            setExistingImages
          }
          onNewImagesChange={
            setNewImages
          }
        />

        {/* Product Fields */}

        {marketplaceType ===
          "product" && (
          <ProductFields
            brand={
              productData.brand
            }
            model={
              productData.model
            }
            condition={
              productData.condition
            }
            quantity={
              productData.quantity
            }
            warranty={
              productData.warranty
            }
            onBrandChange={(
              value
            ) =>
              setProductData(
                (current) => ({
                  ...current,
                  brand: value,
                })
              )
            }
            onModelChange={(
              value
            ) =>
              setProductData(
                (current) => ({
                  ...current,
                  model: value,
                })
              )
            }
            onConditionChange={(
              value
            ) =>
              setProductData(
                (current) => ({
                  ...current,
                  condition:
                    value,
                })
              )
            }
            onQuantityChange={(
              value
            ) =>
              setProductData(
                (current) => ({
                  ...current,
                  quantity:
                    value,
                })
              )
            }
            onWarrantyChange={(
              value
            ) =>
              setProductData(
                (current) => ({
                  ...current,
                  warranty:
                    value,
                })
              )
            }
          />
        )}

        {/* Rental Fields */}
{marketplaceType === "rental" && (
  <RentalFields

    category={
      basicInfo.category
    }

    subCategory={
      basicInfo.subCategory
    }

    rentalPeriod={
      rentalData.rentalPeriod
    }

    condition={
      rentalData.condition
    }

    quantity={
      rentalData.quantity
    }

    securityDeposit={
      rentalData.securityDeposit
    }

    availability={
      rentalData.availability
    }

    propertyType={
      rentalData.propertyType
    }

    bedrooms={
      rentalData.bedrooms
    }

    bathrooms={
      rentalData.bathrooms
    }

    parking={
      rentalData.parking
    }

    furnished={
      rentalData.furnished
    }

    vehicleType={
      rentalData.vehicleType
    }

    make={
      rentalData.make
    }

    model={
      rentalData.model
    }

    year={
      rentalData.year
    }

    transmission={
      rentalData.transmission
    }

    seats={
      rentalData.seats
    }

    equipmentType={
      rentalData.equipmentType
    }

    eventType={
      rentalData.eventType
    }

    onRentalPeriodChange={(value) =>
      setRentalData((current) => ({
        ...current,
        rentalPeriod: value,
      }))
    }

    onConditionChange={(value) =>
      setRentalData((current) => ({
        ...current,
        condition: value,
      }))
    }

    onQuantityChange={(value) =>
      setRentalData((current) => ({
        ...current,
        quantity: value,
      }))
    }

    onSecurityDepositChange={(value) =>
      setRentalData((current) => ({
        ...current,
        securityDeposit: value,
      }))
    }

    onAvailabilityChange={(value) =>
      setRentalData((current) => ({
        ...current,
        availability: value,
      }))
    }

    onPropertyTypeChange={(value) =>
      setRentalData((current) => ({
        ...current,
        propertyType: value,
      }))
    }

    onBedroomsChange={(value) =>
      setRentalData((current) => ({
        ...current,
        bedrooms: value,
      }))
    }

    onBathroomsChange={(value) =>
      setRentalData((current) => ({
        ...current,
        bathrooms: value,
      }))
    }

    onParkingChange={(value) =>
      setRentalData((current) => ({
        ...current,
        parking: value,
      }))
    }

    onFurnishedChange={(value) =>
      setRentalData((current) => ({
        ...current,
        furnished: value,
      }))
    }

    onVehicleTypeChange={(value) =>
      setRentalData((current) => ({
        ...current,
        vehicleType: value,
      }))
    }

    onMakeChange={(value) =>
      setRentalData((current) => ({
        ...current,
        make: value,
      }))
    }

    onModelChange={(value) =>
      setRentalData((current) => ({
        ...current,
        model: value,
      }))
    }

    onYearChange={(value) =>
      setRentalData((current) => ({
        ...current,
        year: value,
      }))
    }

    onTransmissionChange={(value) =>
      setRentalData((current) => ({
        ...current,
        transmission: value,
      }))
    }

    onSeatsChange={(value) =>
      setRentalData((current) => ({
        ...current,
        seats: value,
      }))
    }

    onEquipmentTypeChange={(value) =>
      setRentalData((current) => ({
        ...current,
        equipmentType: value,
      }))
    }

    onEventTypeChange={(value) =>
      setRentalData((current) => ({
        ...current,
        eventType: value,
      }))
    }
  />
)}

        {/* Service Fields */}

        {marketplaceType ===
          "service" && (
          <ServiceFields
            serviceCategory={
              serviceData.serviceCategory
            }
            experience={
              serviceData.experience
            }
            availability={
              serviceData.availability
            }
            serviceArea={
              serviceData.serviceArea
            }
            pricingType={
              serviceData.pricingType
            }
            onServiceCategoryChange={(
              value
            ) =>
              setServiceData(
                (current) => ({
                  ...current,
                  serviceCategory:
                    value,
                })
              )
            }
            onExperienceChange={(
              value
            ) =>
              setServiceData(
                (current) => ({
                  ...current,
                  experience:
                    value,
                })
              )
            }
            onAvailabilityChange={(
              value
            ) =>
              setServiceData(
                (current) => ({
                  ...current,
                  availability:
                    value,
                })
              )
            }
            onServiceAreaChange={(
              value
            ) =>
              setServiceData(
                (current) => ({
                  ...current,
                  serviceArea:
                    value,
                })
              )
            }
            onPricingTypeChange={(
              value
            ) =>
              setServiceData(
                (current) => ({
                  ...current,
                  pricingType:
                    value,
                })
              )
            }
          />
        )}

        {/* Job Fields */}

        {marketplaceType ===
          "job" && (
          <JobFields
            company={
              jobData.company
            }
            position={
              jobData.position
            }
            employmentType={
              jobData.employmentType
            }
            salary={
              jobData.salary
            }
            experience={
              jobData.experience
            }
            applicationDeadline={
              jobData.applicationDeadline
            }
            onCompanyChange={(
              value
            ) =>
              setJobData(
                (current) => ({
                  ...current,
                  company:
                    value,
                })
              )
            }
            onPositionChange={(
              value
            ) =>
              setJobData(
                (current) => ({
                  ...current,
                  position:
                    value,
                })
              )
            }
            onEmploymentTypeChange={(
              value
            ) =>
              setJobData(
                (current) => ({
                  ...current,
                  employmentType:
                    value,
                })
              )
            }
            onSalaryChange={(
              value
            ) =>
              setJobData(
                (current) => ({
                  ...current,
                  salary:
                    value,
                })
              )
            }
            onExperienceChange={(
              value
            ) =>
              setJobData(
                (current) => ({
                  ...current,
                  experience:
                    value,
                })
              )
            }
            onApplicationDeadlineChange={(
              value
            ) =>
              setJobData(
                (current) => ({
                  ...current,
                  applicationDeadline:
                    value,
                })
              )
            }
          />
        )}

        {/* Publish */}

        <div className="mt-8">
          <Button
            className="w-full"
            onClick={
              handlePublish
            }
          >
            {isEditing
              ? "Update Marketplace Item"
              : "Publish Marketplace Item"}
          </Button>
        </div>

      </Container>
    </section>
  );
}