// Write your script here
const attachPaymentLink = async (item_code, qty) => {
  console.log("creating payment link");
  doc = page_data.doc
  const url = `${page_data.url}/api/method/erpnext.accounts.doctype.payment_request.payment_request.make_payment_request?dn=${ doc.name }&dt=${ doc.doctype }&submit_doc=1&order_type=Shopping Cart`;
  const payButton = document.getElementById("pay-button")
    if(payButton){
        payButton.href = url
        console.log("payment link attached")
    } else {
        console.log("payment button not found")
    }
};

document.addEventListener("DOMContentLoaded", attachPaymentLink)