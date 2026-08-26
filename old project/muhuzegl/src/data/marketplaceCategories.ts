import type { IconType } from "react-icons";

export type MarketplaceType =
  | "product"
  | "rental"
  | "service"
  | "job";

export interface MarketplaceSubCategory {
  id: string;
  name: string;
}

export interface MarketplaceCategory {
  id: string;
  name: string;
  icon?: IconType;
  subCategories: MarketplaceSubCategory[];
}

export interface MarketplaceCategoryGroup {
  type: MarketplaceType;
  name: string;
  categories: MarketplaceCategory[];
}

export const marketplaceCategoryGroups: MarketplaceCategoryGroup[] = [
  {
    type: "product",
    name: "Products",

    categories: [
      {
        id: "electronics",
        name: "Electronics",
        subCategories: [
          {
            id: "mobile-phones",
            name: "Mobile Phones",
          },
          {
            id: "laptops-computers",
            name: "Laptops & Computers",
          },
          {
            id: "tablets",
            name: "Tablets",
          },
          {
            id: "smartwatches",
            name: "Smartwatches",
          },
          {
            id: "tvs",
            name: "TVs",
          },
          {
            id: "cameras",
            name: "Cameras",
          },
          {
            id: "audio-speakers",
            name: "Audio & Speakers",
          },
          {
            id: "gaming-consoles",
            name: "Gaming Consoles",
          },
          {
            id: "accessories",
            name: "Accessories",
          },
        ],
      },

      {
        id: "phones-tablets",
        name: "Phones & Tablets",
        subCategories: [
          {
            id: "smartphones",
            name: "Smartphones",
          },
          {
            id: "tablets",
            name: "Tablets",
          },
          {
            id: "smartwatches",
            name: "Smartwatches",
          },
          {
            id: "phone-accessories",
            name: "Phone Accessories",
          },
        ],
      },

      {
        id: "computers-it",
        name: "Computers & IT",
        subCategories: [
          {
            id: "laptops",
            name: "Laptops",
          },
          {
            id: "desktop-computers",
            name: "Desktop Computers",
          },
          {
            id: "monitors",
            name: "Monitors",
          },
          {
            id: "printers",
            name: "Printers",
          },
          {
            id: "networking",
            name: "Networking Equipment",
          },
        ],
      },

      {
        id: "vehicles",
        name: "Vehicles",
        subCategories: [
          {
            id: "cars",
            name: "Cars",
          },
          {
            id: "motorcycles",
            name: "Motorcycles",
          },
          {
            id: "bicycles",
            name: "Bicycles",
          },
          {
            id: "trucks",
            name: "Trucks",
          },
          {
            id: "vehicle-parts",
            name: "Vehicle Parts & Accessories",
          },
        ],
      },

      {
        id: "fashion",
        name: "Fashion & Clothing",
        subCategories: [
          {
            id: "mens-clothing",
            name: "Men's Clothing",
          },
          {
            id: "womens-clothing",
            name: "Women's Clothing",
          },
          {
            id: "childrens-clothing",
            name: "Children's Clothing",
          },
          {
            id: "shoes",
            name: "Shoes",
          },
          {
            id: "bags",
            name: "Bags",
          },
          {
            id: "jewelry",
            name: "Jewelry & Accessories",
          },
        ],
      },

      {
        id: "home-furniture",
        name: "Home & Furniture",
        subCategories: [
          {
            id: "furniture",
            name: "Furniture",
          },
          {
            id: "kitchen",
            name: "Kitchen Equipment",
          },
          {
            id: "home-decoration",
            name: "Home Decoration",
          },
          {
            id: "household-items",
            name: "Household Items",
          },
        ],
      },

      {
        id: "agriculture",
        name: "Agriculture",
        subCategories: [
          {
            id: "farm-products",
            name: "Farm Products",
          },
          {
            id: "seeds",
            name: "Seeds",
          },
          {
            id: "fertilizers",
            name: "Fertilizers",
          },
          {
            id: "farming-equipment",
            name: "Farming Equipment",
          },
          {
            id: "livestock",
            name: "Livestock",
          },
        ],
      },

      {
        id: "health-beauty",
        name: "Health & Beauty",
        subCategories: [
          {
            id: "cosmetics",
            name: "Cosmetics",
          },
          {
            id: "hair-products",
            name: "Hair Products",
          },
          {
            id: "personal-care",
            name: "Personal Care",
          },
        ],
      },

      {
        id: "sports-fitness",
        name: "Sports & Fitness",
        subCategories: [
          {
            id: "sports-equipment",
            name: "Sports Equipment",
          },
          {
            id: "gym-equipment",
            name: "Gym Equipment",
          },
          {
            id: "sports-clothing",
            name: "Sports Clothing",
          },
        ],
      },
    ],
  },

  {
    type: "rental",
    name: "Renting",

    categories: [
      {
        id: "rental-properties",
        name: "Properties",
        subCategories: [
          {
            id: "houses",
            name: "Houses",
          },
          {
            id: "apartments",
            name: "Apartments",
          },
          {
            id: "rooms",
            name: "Rooms",
          },
          {
            id: "offices",
            name: "Offices",
          },
          {
            id: "commercial-buildings",
            name: "Commercial Buildings",
          },
        ],
      },

      {
        id: "rental-vehicles",
        name: "Vehicles",
        subCategories: [
          {
            id: "rental-cars",
            name: "Cars",
          },
          {
            id: "rental-motorcycles",
            name: "Motorcycles",
          },
          {
            id: "rental-bicycles",
            name: "Bicycles",
          },
          {
            id: "rental-trucks",
            name: "Trucks",
          },
        ],
      },

      {
        id: "rental-equipment",
        name: "Equipment",
        subCategories: [
          {
            id: "construction-equipment",
            name: "Construction Equipment",
          },
          {
            id: "farming-equipment-rental",
            name: "Farming Equipment",
          },
          {
            id: "event-equipment",
            name: "Event Equipment",
          },
          {
            id: "industrial-equipment",
            name: "Industrial Equipment",
          },
        ],
      },

      {
        id: "rental-electronics",
        name: "Electronics",
        subCategories: [
          {
            id: "rental-cameras",
            name: "Cameras",
          },
          {
            id: "projectors",
            name: "Projectors",
          },
          {
            id: "sound-systems",
            name: "Sound Systems",
          },
          {
            id: "rental-computers",
            name: "Computers",
          },
        ],
      },

      {
        id: "event-party",
        name: "Event & Party",
        subCategories: [
          {
            id: "chairs-tables",
            name: "Chairs & Tables",
          },
          {
            id: "tents",
            name: "Tents",
          },
          {
            id: "event-decoration",
            name: "Decoration Equipment",
          },
          {
            id: "sound-lighting",
            name: "Sound & Lighting",
          },
        ],
      },
    ],
  },

  {
    type: "service",
    name: "Services",

    categories: [
      {
        id: "technology",
        name: "Technology",
        subCategories: [
          {
            id: "web-development",
            name: "Web Development",
          },
          {
            id: "app-development",
            name: "App Development",
          },
          {
            id: "graphic-design",
            name: "Graphic Design",
          },
          {
            id: "it-support",
            name: "IT Support",
          },
          {
            id: "networking-services",
            name: "Networking",
          },
        ],
      },

      {
        id: "construction-services",
        name: "Construction",
        subCategories: [
          {
            id: "building",
            name: "Building",
          },
          {
            id: "plumbing",
            name: "Plumbing",
          },
          {
            id: "electrical",
            name: "Electrical",
          },
          {
            id: "painting",
            name: "Painting",
          },
          {
            id: "carpentry",
            name: "Carpentry",
          },
        ],
      },

      {
        id: "transport-services",
        name: "Transport",
        subCategories: [
          {
            id: "moving",
            name: "Moving",
          },
          {
            id: "delivery",
            name: "Delivery",
          },
          {
            id: "taxi",
            name: "Taxi",
          },
          {
            id: "logistics",
            name: "Logistics",
          },
        ],
      },

      {
        id: "business-services",
        name: "Business",
        subCategories: [
          {
            id: "marketing",
            name: "Marketing",
          },
          {
            id: "accounting",
            name: "Accounting",
          },
          {
            id: "consulting",
            name: "Consulting",
          },
          {
            id: "business-support",
            name: "Business Support",
          },
        ],
      },

      {
        id: "home-services",
        name: "Home Services",
        subCategories: [
          {
            id: "cleaning",
            name: "Cleaning",
          },
          {
            id: "gardening",
            name: "Gardening",
          },
          {
            id: "repairs",
            name: "Repairs",
          },
          {
            id: "maintenance",
            name: "Maintenance",
          },
        ],
      },

      {
        id: "beauty-services",
        name: "Beauty",
        subCategories: [
          {
            id: "hairdressing",
            name: "Hairdressing",
          },
          {
            id: "makeup",
            name: "Makeup",
          },
          {
            id: "nail-services",
            name: "Nail Services",
          },
          {
            id: "salon-services",
            name: "Salon Services",
          },
        ],
      },

      {
        id: "education-services",
        name: "Education",
        subCategories: [
          {
            id: "tutoring",
            name: "Tutoring",
          },
          {
            id: "languages",
            name: "Languages",
          },
          {
            id: "computer-training",
            name: "Computer Training",
          },
          {
            id: "professional-training",
            name: "Professional Training",
          },
        ],
      },
    ],
  },

  {
    type: "job",
    name: "Jobs",

    categories: [
      {
        id: "technology-jobs",
        name: "Technology",
        subCategories: [
          {
            id: "software-developer",
            name: "Software Developer",
          },
          {
            id: "web-developer",
            name: "Web Developer",
          },
          {
            id: "it-support-job",
            name: "IT Support",
          },
          {
            id: "network-engineer",
            name: "Network Engineer",
          },
        ],
      },

      {
        id: "sales-marketing-jobs",
        name: "Sales & Marketing",
        subCategories: [
          {
            id: "sales-agent",
            name: "Sales Agent",
          },
          {
            id: "digital-marketing",
            name: "Digital Marketing",
          },
          {
            id: "business-development",
            name: "Business Development",
          },
          {
            id: "marketing-job",
            name: "Marketing",
          },
        ],
      },

      {
        id: "finance-jobs",
        name: "Finance",
        subCategories: [
          {
            id: "accountant",
            name: "Accountant",
          },
          {
            id: "finance-officer",
            name: "Finance Officer",
          },
          {
            id: "auditor",
            name: "Auditor",
          },
        ],
      },

      {
        id: "construction-jobs",
        name: "Construction",
        subCategories: [
          {
            id: "engineer",
            name: "Engineer",
          },
          {
            id: "mason",
            name: "Mason",
          },
          {
            id: "electrician",
            name: "Electrician",
          },
          {
            id: "plumber",
            name: "Plumber",
          },
        ],
      },

      {
        id: "transport-jobs",
        name: "Transport",
        subCategories: [
          {
            id: "driver",
            name: "Driver",
          },
          {
            id: "delivery-agent",
            name: "Delivery Agent",
          },
          {
            id: "logistics-job",
            name: "Logistics",
          },
        ],
      },

      {
        id: "hospitality-jobs",
        name: "Hospitality",
        subCategories: [
          {
            id: "hotel-staff",
            name: "Hotel Staff",
          },
          {
            id: "restaurant-staff",
            name: "Restaurant Staff",
          },
          {
            id: "chef",
            name: "Chef",
          },
        ],
      },

      {
        id: "education-jobs",
        name: "Education",
        subCategories: [
          {
            id: "teacher",
            name: "Teacher",
          },
          {
            id: "tutor",
            name: "Tutor",
          },
          {
            id: "trainer",
            name: "Trainer",
          },
        ],
      },

      {
        id: "other-jobs",
        name: "Other Jobs",
        subCategories: [
          {
            id: "other-job",
            name: "Other",
          },
        ],
      },
    ],
  },
];

export function getCategoriesByMarketplaceType(
  type: MarketplaceType
): MarketplaceCategory[] {
  return (
    marketplaceCategoryGroups.find(
      (group) => group.type === type
    )?.categories ?? []
  );
}