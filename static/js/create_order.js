document.addEventListener('DOMContentLoaded', function() {
    var order_data = [];
    var addStockButtons = document.querySelectorAll('.add');
    var removeStockButtons = document.querySelectorAll('.remove');
    var submit_btn = document.querySelector(".submit_btn")


    function make_order(btn_type, item_name, brand_name) {
        if (btn_type === "add") {
            var existingItem = order_data.find(item => item.item_name === item_name);
            if (existingItem) {
                existingItem.quantity += 1;
            }
            else {
                var order = { item_name: item_name, brand_name: brand_name, quantity: 1 };
                order_data.push(order);
            }
        } 
        else {
            var existingItem = order_data.find(item => item.item_name === item_name);

            if (existingItem) {
                if (existingItem.quantity === 1) {
                    order_data = order_data.filter(item => item.item_name !== item_name);
                } else {
                    existingItem.quantity -= 1;
                    if (existingItem.quantity == 0);{
                        order_data.pop(order)
                    }
                }
            }
        }
    }

    addStockButtons.forEach(function(button) {
        button.addEventListener("click", function(event) {
            event.preventDefault();
            var row = button.closest("tr");
            var item_name = row.querySelector(".item_name").textContent;
            var brand_name = row.querySelector(".brand_name").textContent;
            var quantityCell = row.querySelector(".quant");
            var btn_type = "add";
            var currentQuantity = parseInt(quantityCell.textContent, 10) || 0;
            quantityCell.textContent = currentQuantity + 1;
            make_order(btn_type, item_name, brand_name, currentQuantity);
        });
    });

    removeStockButtons.forEach(function(button) {
        button.addEventListener("click", function(event) {
            event.preventDefault();
            var row = button.closest("tr");
            var item_name = row.querySelector(".item_name").textContent;
            var brand_name = row.querySelector(".brand_name").textContent;
            var quantityCell = row.querySelector(".quant");
            var btn_type = "sub";
            var currentQuantity = parseInt(quantityCell.textContent, 10) || 0;

            if (currentQuantity >= 1) {
                quantityCell.textContent = currentQuantity - 1;
            }

            make_order(btn_type, item_name, brand_name, currentQuantity );

        });
    });
    submit_btn.addEventListener("click", async function(e){
        e.preventDefault()
        try{
            const response = await fetch("/oders",{
                method : "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                
                body:JSON.stringify({ data: order_data})
            })
            if (response.ok){
                window.location.href = "/order/list/0";
            }
            else {
            const errorData = await response.json();
            console.error("Error submitting order:", errorData.message);
        }
        }
        catch(error){
            console.error(error)
        }
    })
})
    
