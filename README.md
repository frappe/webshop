# Frappe Webshop
Frappe Webshop is an Open Source eCommerce Platform, developed primarily using Python and JavaScript. Frappe Webshop was developed as part of the Frappe framework, which is designed to help developers quickly create business applications with minimal code by offering a combination of easy to use front-end and back-end development tools. Frappe Webshop is specifically targeted to help *small to medium sized businesses* with increasing their digital presence and being able to easily create online stores for their brands. Frappe Webshop can be integrated with ERPNext, which is an enterprise resource planning system used by businesses to record all their transactions in a single system. Frappe Webshop emphasizes simplicity, customization, and clean interfaces, providing businesses with the ability to create a tailored user experience both efficently and for free. 
## Table of Contents
- [Table of Contents](https://github.com/frappe/webshop#table-of-contents)
- [Why choose Frappe Webshop?](https://github.com/frappe/webshop/#why-choose-frappe-webshop)
- [Example Frappe Webshop Interface](https://github.com/frappe/webshop/#example-frappe-webshop-interface)
- [Features](https://github.com/frappe/webshop/#features)
- [Setup](https://github.com/frappe/webshop/#setup)
    - [Installation using Docker](https://github.com/frappe/webshop/#installation-using-docker)
    - [Easy Install Script](https://github.com/frappe/webshop/#easy-install-script)
    - [Manual Installation](https://github.com/frappe/webshop/#manual-installation)
- [Usage](https://github.com/frappe/webshop/#usage)
- [Contributing](https://github.com/frappe/webshop/#contributing)
- [License](https://github.com/frappe/webshop/#license)

## Why choose Frappe Webshop?
- **Fast and Efficient**: Streamlined online sales process, offering a shopping experience that can quickly be developed to meet the needs of any business.

- **Personalized and Customizable**: Webshops are highly customizable, providing features and designs that businesses choose and allowing for effective customer engagement with the products.

- **Dynamic and Scalable**: Webshops can be easily adapted to fit business goals and to provide a seamless user experience for businesses small and large.

- **Ease of use**: Wesbhop is designed to require minimal technical knowledge for developers, making it accessible for any business looking to develop an online commerce presence.

- **Control and security**: Webshop is self-hosted, meaning that businesses have complete control over their own data and providing a secure environment for customer data.
  
- **Open source**: The Webshop platform is completely *free* to use, providing a cost-effective way for businesses to develop digital storefronts and market their brands online. Being open source also means that there are continuous improvements being made to the platform.

## Example Frappe Webshop Interface
![Frappe Webshop](webshop.png)

## Features
- **Product Management**: Add, edit, and manage products with the ability to add descriptions, images, variants, and inventory counts.
    - **Inventory Control**: Real-time stock updates to ensure that product supply can be easily tracked.
- **Multiple Payment Options**: Integration with popular payment options like Paypal or Stripe, allowing secure and convenient transactions.
- **User Accounts**: Customers can create accounts and save their information, allowing for convenient checkout and personalized experiences.
    - **Wishlist and Cart Functions**: Let customers save their favorites and revisit them later for easier purchases.
    - **Order Tracking**: Keep customers informed and provide updates on the status of their orders.
- **Advanced Search and Filters**: Advanced search tools and product filters to allow customers to quickly find products they want.
- **Customer Reviews and Ratings**: Customers can share their experiences and product ratings.
- **Integration with ERPNext**: Integration with ERPNext allows for management of inventory, billing, and order processing in one place.
- **User-friendly interface**: Frappe Webshop emphasizes ease of use, with a focus on creating simple, yet effective websites.

## Setup
1. Install [bench](https://github.com/frappe/bench).
   #### Installation using Docker
   ```sh
   $ git clone https://github.com/frappe/frappe_docker.git
   $ cd frappe_docker
   ```
   See more details here: [Containerized Installation](https://github.com/frappe/bench#containerized-installation)
   #### Easy Install Script
   ```sh
   $ wget https://raw.githubusercontent.com/frappe/bench/develop/easy-install.py
   $ python3 easy-install.py --prod --email your@email.tld
   ```
   See more details here: [Easy Install Script](https://github.com/frappe/bench#easy-install-script)
   #### Manual Installation (*recommended only for local development*)
   ```sh
   $ pip install frappe-bench
   ```
   See more details here: [Manual Installation](https://github.com/frappe/bench#manual-installation)

   ##### Bench
   More information on [usage of bench and its commands](https://github.com/frappe/bench#basic-usage).
2. Install ERPNext (only required if bench was installed using manual installation).
3. Once ERPNext is installed, add the webshop app to your bench by running

    ```sh
    $ bench get-app webshop
    ```
4. After that, you can install the webshop app on the required site by running
    ```sh
    $ bench --site sitename install-app webshop
    ```

## Usage
Once setup has been completed, eCommerce features can be set up. This [guide](https://docs.erpnext.com/docs/user/manual/en/set_up_e_commerce) explains how to begin setup of the eCommerce features in conjunction with ERPNext. Many common features and customization options are explained, providing a solid framework for users to get started with building their eCommerce platforms. Note that for best results, users should have some Items setup using ERPNext before attempting to create a store. Creating items is a simple process that can be done through the Webshop interface by accessing > Home > Stock > Items and Pricing > Item.

## Contributing
To contribute to the development of the Frappe Webshop, please make a fork of this repository and make edits within the forked repository. Once satisfied that a contribution should be deployed, create a pull request from your forked repository to this repository. Changes that are accepted will be merged into the main development branch and thus be rolled out to users. To make changes using the bench command line interface, make a clone of this repo using the following command:
```sh
$ git clone https://github.com/frappe/webshop.git
```
For more information on using the bench command line interface, please reference this [page](https://github.com/frappe/bench#development).

## License
Licensed under the GNU GENERAL PUBLIC LICENSE V3. This is an open-source project meant to help businesses create online commerce platforms. (See [LICENSE](LICENSE) for more information).
