import Hero from "../../components/home/Hero";
import Categories from "../../components/home/Categories";
import Offers from "../../components/home/Offers";
import FeaturedProducts from "../../components/home/FeaturedProducts";
import WhyChoose from "../../components/home/whyChoose";
import TopSellers from "../../components/home/TopSellers";
import Testimonials from "../../components/home/Testimonials";
import Newsletter from "../../components/home/NewsLetter/Newsletter";




export default function Home() {

  return (
    <>
      {/* Temporary Test Button */}
      

      <Hero />

      <Categories />

      <Offers />

      <FeaturedProducts />

      <WhyChoose />

      <TopSellers />

      <Testimonials />

      <Newsletter />

    </>
  );
}