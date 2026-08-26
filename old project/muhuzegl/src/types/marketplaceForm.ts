export interface BasicInfo {
  title: string;
  description: string;
  category: string;
  subCategory: string;
  price: string;
  location: string;
  images: File[];
}

export interface ProductData {
  brand: string;
  model: string;
  condition: string;
  quantity: string;
  warranty: string;
}

export interface RentalData {
  /*
   * Common rental information
   */
  rentalPeriod: string;
  condition: string;
  quantity: string;
  securityDeposit: string;
  availability: string;

  /*
   * Property rental
   */
  propertyType: string;
  bedrooms: string;
  bathrooms: string;
  parking: string;
  furnished: boolean;

  /*
   * Vehicle rental
   */
  vehicleType: string;
  make: string;
  model: string;
  year: string;
  transmission: string;
  seats: string;

  /*
   * Equipment rental
   */
  equipmentType: string;

  /*
   * Event & Party rental
   */
  eventType: string;
}

export interface ServiceData {
  serviceCategory: string;
  experience: string;
  availability: string;
  serviceArea: string;
  pricingType: string;
}

export interface JobData {
  company: string;
  position: string;
  employmentType: string;
  salary: string;
  experience: string;
  educationLevel: string;
  skillsRequired: string;
  recruiterContact: string;
  applicationDeadline: string;
}