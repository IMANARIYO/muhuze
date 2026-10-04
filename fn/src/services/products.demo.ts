import type { Product } from '@/types/product'

// Demo listings used only while VITE_API_URL is unset. Delete with the backend connection.
const img = (id: string) =>
  `https://images.unsplash.com/photo-${id}?w=640&q=70&auto=format&fit=crop`

const row = (
  id: number, title: string, type: Product['type'], category: string, price: number,
  image: string, views: number, uses: number, seller: string, contact: string | null, unit?: string,
): Product => ({
  id, title, type, category, price, unit, image: img(image), views, uses,
  description: `${title} listed by ${seller}. Verified listing on Muhuze with fast response from the seller.`,
  seller: { name: seller, contact },
})

export const demoProducts: Product[] = [
  row(1, 'Smartphone 128GB, dual SIM', 'sale', 'Phones', 420000, '1511707171634-5f897ff02aa9', 4820, 312, 'Kigali Mobile', '+250 788 000 111'),
  row(2, 'Wireless studio headphones', 'sale', 'Audio', 95000, '1505740420928-5e560c06d30e', 2310, 148, 'SoundHub', '+250 788 000 222'),
  row(3, 'Classic minimalist watch', 'sale', 'Fashion', 68000, '1523275335684-37898b6baf30', 1975, 96, 'Timeless', '+250 788 000 333'),
  row(4, 'Running sneakers', 'sale', 'Fashion', 54000, '1542291026-7eec264c27ff', 3640, 207, 'Stride Store', '+250 788 000 444'),
  row(5, 'Instant film camera', 'sale', 'Cameras', 130000, '1526170375885-4d8ecf77b99f', 1284, 41, 'Lens & Co', '+250 788 000 555'),
  row(6, 'Ultrabook laptop 14"', 'sale', 'Computers', 890000, '1496181133206-80ce9b88a853', 5102, 88, 'TechPoint', '+250 788 000 666'),
  row(7, 'Family house, 4 bedrooms', 'rental', 'Houses', 650000, '1568605114967-8130f3a36994', 6230, 12, 'Prime Homes', null, 'month'),
  row(8, 'Furnished city apartment', 'rental', 'Apartments', 380000, '1502672260266-1c1ef2d93688', 4411, 27, 'Urban Stay', '+250 788 000 888', 'month'),
  row(9, 'Sports coupe for weekends', 'rental', 'Cars', 85000, '1494976388531-d1058494cdd8', 3907, 64, 'DriveNow', '+250 788 000 999', 'day'),
  row(10, 'Barber: haircut and beard', 'service', 'Beauty', 5000, '1503951914875-452162b0f3f1', 2788, 530, 'Fresh Cuts', null, 'session'),
  row(11, 'Private chef for events', 'service', 'Cooking', 60000, '1556910103-1c02745aae4d', 1650, 73, 'Chef Aline', '+250 788 000 123', 'event'),
  row(12, 'Online job application help', 'service', 'Careers', 10000, '1521737604893-d14cc237f11d', 2144, 189, 'CareerLift', '+250 788 000 456', 'application'),
]
