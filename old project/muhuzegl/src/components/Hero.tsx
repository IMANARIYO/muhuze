function Hero(){

    return (

        <section className="hero">

            <div className="hero-content">

                <h1>
                    Buy, Sell & Connect 
                    <span> Anywhere</span>
                </h1>

                <p>
                    MUHUZE Global Link is your trusted marketplace 
                    to discover products, connect with sellers, 
                    and grow your business online.
                </p>


                <div className="hero-search">

                    <input 
                    type="text"
                    placeholder="Search products..."
                    />

                    <button>
                        Search
                    </button>

                </div>


                <div className="hero-buttons">

                    <button className="shop-btn">
                        Start Shopping
                    </button>


                    <button className="sell-btn">
                        Sell Your Product
                    </button>

                </div>


            </div>


            <div className="hero-image">

                <img 
                src="/marketplace.png"
                alt="Marketplace"
                />

            </div>


        </section>

    )

}


export default Hero;